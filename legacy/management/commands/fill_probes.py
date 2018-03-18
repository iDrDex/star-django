import sys
import shutil
import subprocess
import os.path
import re
import ftplib
import socket
import threading
import gzip
import time
from itertools import compress
import io
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.db.models import Q

from funcy import re_find, re_test, re_iter, group_values, walk_values, \
    decorator, contextmanager, cached_property, retry, suppress, log_errors, print_durations, \
    take, cat, lcat, keep, lkeep, remove, lremove, lpluck, ldistinct, chunks
from cacheops import file_cache
from termcolor import cprint
from ftptool import FTPHost
import pandas as pd
import mygene
import requests

from legacy.models import Platform, PlatformProbe


SOCKET_TIMEOUT = 20
CACHE_TIMEOUT = 4 * 24 * 60 * 60
CACHEOPS_DEBUG = True  # Makes function cache keys not depend on line no

GEO_HOST = 'ftp.ncbi.nih.gov'
LINUX_BLAT = 'http://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/blat/blat'
REFMRNA_URLS = {
    'human': 'http://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/refMrna.fa.gz',
    'mouse': 'http://hgdownload.soe.ucsc.edu/goldenPath/mm10/bigZips/refMrna.fa.gz',
    'rat': 'http://hgdownload.soe.ucsc.edu/goldenPath/rn6/bigZips/refMrna.fa.gz',
}


class Command(BaseCommand):
    help = 'Fills in missing platform probes'

    def add_arguments(self, parser):
        parser.add_argument('--ipdb', action='store_true', help='Drop into ipdb in error')
        parser.add_argument('--id', type=int, help='Fill platform with this id')
        parser.add_argument('--recheck', action='store_true', help='Try to refill failed platforms')
        parser.add_argument('--redo', type=int, help='Refill the oldest REDO platforms')
        parser.add_argument('--plain', action='store_true', help='No colors nor progress bars')

    def handle(self, **options):
        # Set up debugger
        if options['ipdb']:
            import sys, ipdb, traceback  # noqa

            def info(type, value, tb):
                traceback.print_exception(type, value, tb)
                print()
                ipdb.pm()
            sys.excepthook = info

        if options['plain']:
            global cprint, tqdmio

            def cprint(message, *args, **kwargs):
                print(message)

            class tqdmio:
                def __init__(self, desc=None, **kwargs):
                    print(desc)

                def __enter__(self):
                    return self

                def __exit__(self, typ, exc, trace):
                    pass

                def wrap(self, f):
                    return f

        if options['id']:
            fill_probes(options['id'])
            return

        if options['redo']:
            old = timezone.now() - timedelta(days=120)
            qs = Platform.objects.filter(Q(last_filled=None) | Q(last_filled__lt=old)) \
                                 .order_by('pk')[:options['redo']]
        elif options['recheck']:
            qs = Platform.objects.exclude(verdict='ok').order_by('-pk')
        else:
            qs = Platform.objects.filter(verdict='').order_by('-pk')

        for pk in qs.values_list('pk', flat=True):
            fill_probes(pk)


@print_durations
def fill_probes(platform_id):
    platform = Platform.objects.get(pk=platform_id)
    gpl_name = platform.gpl_name
    cprint('%s %s %s' % (platform.pk, platform.gpl_name, platform.specie), attrs=['bold'])
    assert platform.specie

    platform.verdict = ''
    platform.probes_total = None
    platform.probes_matched = None
    platform.stats = {}
    platform.last_filled = timezone.now()

    annot_file = '/pub/geo/DATA/annotation/platforms/%s.annot.gz' % gpl_name
    family_file = '/pub/geo/DATA/SOFT/by_platform/%s/%s_family.soft.gz' % (gpl_name, gpl_name)
    files = [annot_file, family_file]
    tables = list(map(peek_platform, files))
    # Skip empty
    files = list(compress(files, tables))
    tables = lkeep(tables)

    # TODO: check other supplementary files formats
    supplementary_dir = '/pub/geo/DATA/supplementary/platforms/%s/' % gpl_name
    _, supplementary_files = listdir(supplementary_dir)
    supplementary_files = [f for f in supplementary_files
                           if f.endswith('.txt.gz') and not re_test('\.cdf\.', f, re.I)]
    files.extend(supplementary_files)
    tables.extend(decompress(download('%s%s' % (supplementary_dir, f)))
                  for f in supplementary_files)
    platform.stats['files'] = lkeep(files)

    if not any(tables):
        cprint('No data for %s' % gpl_name, 'red')
        platform.verdict = 'no data'
        platform.save()
        return

    # Read tables in
    df = pd.concat(read_table(table, file) for table, file in zip(tables, files))
    del tables  # free memory
    platform.probes_total = len(set(df.index))
    cprint('Found %d probes to match' % platform.probes_total, 'yellow')
    # import ipdb; ipdb.set_trace()  # noqa

    # Try to resolve probes starting from best scopes
    mygene_probes = []
    platform.stats['matches'] = []
    platform.verdict = 'no clue'
    for scopes, cols in SCOPE_COLUMNS:
        cols = list(set(cols) & set(df.columns))
        if not cols:
            continue
        cprint('> Looking into %s' % ', '.join(sorted(cols)), 'cyan')
        platform.verdict = 'nothing matched'

        probes = pd.concat(df[col].dropna() for col in cols)
        new_matches = mygene_fetch(platform, probes, scopes)
        mygene_probes.extend(new_matches)

        # Drop matched probes
        if new_matches:
            platform.stats['matches'].append({
                'scopes': scopes, 'cols': cols,
                'found': len(new_matches),
            })

            df = df.drop(lpluck('probe', new_matches))
            if df.empty:
                break

    # Update stats and history
    platform.probes_matched = len(mygene_probes)
    platform.history.append({
        'time': timezone.now().strftime('%Y-%m-%d %T'),
        'probes_total': platform.probes_total,
        'probes_matched': platform.probes_matched,
    })

    # Insert found genes
    if mygene_probes:
        with transaction.atomic():
            platform.verdict = 'ok'
            platform.save()

            platform.probes.all().delete()
            PlatformProbe.objects.bulk_create([
                PlatformProbe(platform=platform, **probe_info)
                for probe_info in mygene_probes
            ])
        cprint('Inserted %d probes for %s' % (len(mygene_probes), gpl_name), 'green')
    else:
        cprint('Nothing matched for %s' % gpl_name, 'red')
        platform.save()


# Ordered by priority
SCOPE_COLUMNS = (
    ('dna', ['sequence', 'platform_sequence', 'probe_sequence', 'probeseq', 'mature_sequence',
             'probeset_target_sequence']),
    ('unigene', ['unigene_id', 'unigene', 'clusterid', 'cluster_id', 'cluster_id_unigene',
                 'unigene_cluster_id']),
    ('refseq', ['refseq', 'refseq_transcript_id', 'representative_public_id']),
    ('accession', ['gb_acc', 'gene_bank_acc', 'gene_bank_accession', 'gen_bank_accession',
                   'genbank_accession', 'gb_list', 'acc_no', 'accession',
                   'unigene_accession']),
    ('symbol,alias', ['gene_symbol', 'unigene_symbol', 'symbol', 'genesymbol', 'gene',
                      'ilmn_gene', 'gene_symbols', 'unigene_gene_symbol', 'clone_id']),
    ('entrezgene,retired', ['entrez', 'entrez_id', 'entrez_gene', 'entrez_gene_id']),
    ('ensemblgene,ensembltranscript',
        ['ensembl', 'ensembl_id', 'ensemblid' 'ensembl_gene', 'ensembl_gene_id', 'ensg_id',
         'transcript_id', 'geneids_ensmusg']),
    ('unigene,symbol,alias', ['compositesequence_identifier', 'compositesequence_name']),
    ('entrezgene,retired,ensemblgene', ['gene_id', 'gene_ids', 'geneid_locusid']),
    ('entrezgene,retired,ensemblgene,symbol,alias', ['orf', 'orf_list']),
    ('symbol,alias,other_names', ['reporter_name', 'gene_name', 'mirna_id', 'mirna_id_list']),
    ('symbol,alias,refseq,accession,ensemblgene,ensembltranscript,unigene',
        ['primary_sequence_name', 'sequence_code', 'sequence_name_s', 'spot_id', 'seq_id',
         'geneids']),
)
SCOPE_CHECK = {
    'unigene': r'^[A-Za-z]+\.\d+$',
    'refseq': r'^[A-Z]+_\d+$',
    'accession': r'^[A-Z]+_?[\d.]+$',
    'symbol': r'^([A-Za-z0-9][A-Za-z0-9_/()<>;.+-]*[A-Za-z0-9>@]|[A-Za-z])$',
    'entrezgene': r'^\d+$', 'retired': r'^\d+$',
    'ensembl': r'^ENS[A-Z]+\d+$',
}
SCOPE_CHECK['alias'] = SCOPE_CHECK['other_names'] = SCOPE_CHECK['symbol']
TRASH_COLUMS = {
    'chromosome', 'chromosome_annotation', 'chromosome_location', 'unigene_chromosome',
    'gene_title', 'nucleotide_title', 'unigene_gene_name', 'unigene_title',
    'gi', 'platform_spotid', 'tissue',
    'go_component', 'go_component_id', 'go_function', 'go_function_id', 'go_process',
    'go_process_id',
    'penat', 'rowat', 'columnat', 'block', 'row', 'column', 'platepos',
    # Names
    'clonetitle'
}
# 'platform_cloneid', 'platform_orf' - check more
# chromosomechromosomestart, chromosomeend, formsthatutilizeprobeset, orientation, targetid_at
# uniqueprobesinset, platepos, plateId, start, stop, chr, position, snp_id, type
# probeset_name,  probeset

# 2971, 358, 37, 344, 598, 876, 891, 998,
# Success - 484,

def newcols(df):
    known_cols = set(cat(cols for _, cols in SCOPE_COLUMNS)) | TRASH_COLUMS
    return lremove(known_cols, df.columns)


def mygene_fetch(platform, probes, scopes):
    """Queries mygene.info for current entrezid and sym, given an identifier."""
    if scopes == "dna":
        probes = get_dna_probes(platform, probes)
        scopes = "accession"

    def extract_queries(lines):
        lines = remove(r'^(IMAGE:\d+|--[\w>-]+)$', lines)
        queries = cat(re_iter(r'[\w+.-]+', l) for l in lines)
        queries = remove(r'_at$|^\d+-\d+$', queries)  # No such thing
        return queries
        # Clean unicode for mygene
        # http://stackoverflow.com/questions/15321138/removing-unicode-u2026-like-characters
        return [q.decode('unicode_escape').encode('ascii', 'ignore') for q in queries]

    _by_probe = group_values(probes.items())
    queries_by_probe = walk_values(extract_queries, _by_probe)

    # Collect all possible queries to make a single request to mygene
    queries = set(cat(queries_by_probe.values()))

    if not queries:
        return []
    mygenes = _mygene_fetch(queries, scopes, platform.specie)

    # Form results into rows
    results = []
    dups = 0
    for probe, queries in queries_by_probe.items():
        matches = ldistinct(keep(mygenes.get, queries))
        # Skip dups
        if len(matches) > 1:
            dups += 1
        elif matches:
            entrez, sym = matches[0]
            results.append({
                'probe': probe, 'mygene_sym': sym, 'mygene_entrez': entrez
            })
    if dups:
        cprint('-> Produced %d dups' % dups, 'red')
    return results


import pickle
import redis
redis_client = redis.StrictRedis.from_url('redis://localhost/2')

# Fill in prefixes to be shorter
SPECIE_PREFIXES = {'human': 'h', 'rat': 'r', 'mouse': 'm'}
PREFIXES = {
    'ensemblgene': 'eg', 'ensembltranscript': 'et',
    'symbol,alias,refseq,accession,ensemblgene,ensembletranscript,unigene': 'shit',
}
for scopes, _ in SCOPE_COLUMNS:
    if scopes not in PREFIXES:
        prefix = ''.join(w[0] for w in scopes.split(','))
        assert prefix not in PREFIXES.values(), 'Dup prefix %s for %s' % (prefix, scopes)
        PREFIXES[scopes] = prefix

def mget(keys):
    return lcat(redis_client.mget(chunk) for chunk in chunks(10000, keys))


@log_errors(lambda msg: cprint(msg, 'red'), stack=False)
@retry(50, errors=requests.HTTPError, timeout=60)
def _mygene_fetch(queries, scopes, specie):
    cprint('> Going to query %d genes in %s...' % (len(queries), scopes), 'cyan')
    cprint('>     sample queries: %s' % ', '.join(take(8, queries)), 'cyan')
    # Read cache
    prefix = '%s-%s:' % (SPECIE_PREFIXES[specie], PREFIXES[scopes])
    keys = [prefix + q for q in queries]
    res = {k: pickle.loads(v) if v else ''
           for k, v in zip(queries, mget(keys))
           if v is not None}
    if res:
        queries = set(queries) - set(res)
        print(('Got %d from cache, %d queries left' % (len(res), len(queries))))

    if queries:
        fields = ['entrezgene', 'symbol']
        mg = mygene.MyGeneInfo()
        data = mg.querymany(queries, scopes=scopes, fields=fields,
                            species=specie, email='suor.web@gmail.com')
        new = {str(item['query']): (item['entrezgene'], item['symbol'])
               for item in data
               if not item.get('notfound') and 'entrezgene' in item and 'symbol' in item}
        res.update(new)
        # Cache results and fails
        pipe = redis_client.pipeline(transaction=False)
        for k, v in new.items():
            pipe.setex(prefix + k, CACHE_TIMEOUT, pickle.dumps(v, -1))
        for k in queries - set(new):
            pipe.setex(prefix + k, CACHE_TIMEOUT, '')
        pipe.execute()

    res = {k: v for k, v in res.items() if v != ''}
    cprint('-> Got %d matches' % len(res), 'yellow')
    return res


def get_dna_probes(platform, probes):
    # Suppress a warning caused by SearchIO import
    from Bio import BiopythonExperimentalWarning
    import warnings
    warnings.simplefilter('ignore', BiopythonExperimentalWarning)

    from Bio import SearchIO

    cprint('> Going to blat %d sequences' % len(probes), 'cyan')

    _ensure_files_dir()
    blat = _ensure_blat()
    refmrna = _ensure_refmrna(platform.specie)

    # Write probes file
    probes_name = os.path.join(settings.BASE_DIR, "_files/%s.probes" % platform.gpl_name)
    with open(probes_name + ".fa", "w") as f:
        # Using numeric idents here cause probe names can contain spaces
        i_to_probe = {str(i): probe for i, probe in enumerate(probes.index)}
        f.write("\n".join('>%s\n%s' % (i, seq) for i, seq in enumerate(probes)))

    # Match sequences
    probes_fa = probes_name + ".fa"
    probes_psl = probes_name + "-refMrna.psl"
    psl_written = False
    if not os.path.isfile(probes_psl):  # Simple caching
        cmd = """{blat}
                 {refmrna}
                 -stepSize=5
                 -repMatch=2253
                 -minScore=0
                 -minIdentity=0
                 {probes_fa} {probes_psl}""".format(**locals())
        print("BLATTING RefSeq mRNAs...")
        with print_durations('blatting ' + platform.gpl_name):
            output = subprocess.check_call(cmd.split(), stdout=sys.stdout, stderr=sys.stderr)
            psl_written = True

    # Parse results
    try:
        print("Parsing %s psl..." % platform.gpl_name)
        with print_durations('parsing ' + platform.gpl_name):
            parser = SearchIO.parse(probes_psl, "blat-psl")
            data = {}
            for result in parser:
                best_hit = max(result, key=lambda hit: max(hsp.score for hsp in hit))
                data[i_to_probe[best_hit.query_id]] = best_hit.id
    except AssertionError:
        # Failed parsing, probably broken psl
        if psl_written:
            raise
        os.remove(probes_psl)
        return get_dna_probes(platform, probes)

    return pd.Series(data)


def _ensure_files_dir():
    _files_dir = os.path.join(settings.BASE_DIR, '_files')
    if not os.path.exists(_files_dir):
        os.mkdir(_files_dir)


def _ensure_blat():
    blat_file = os.path.join(settings.BASE_DIR, '_files/blat')
    if not os.path.isfile(blat_file):
        cprint('Downloading blat...', 'blue')
        http_to_file(LINUX_BLAT, blat_file)
        os.chmod(blat_file, 0o755)
    return blat_file


@retry(50, errors=requests.HTTPError, timeout=30)
def _ensure_refmrna(specie):
    specie_refmrna = os.path.join(settings.BASE_DIR, '_files/%s.fa' % specie)
    if not os.path.isfile(specie_refmrna):
        cprint('Downloading %s refMrna...' % specie, 'blue')
        http_to_file(REFMRNA_URLS[specie], specie_refmrna + '.gz')
        subprocess.check_call(['gzip', '-d', specie_refmrna + '.gz'],
                              stdout=sys.stdout, stderr=sys.stderr)
    return specie_refmrna


@retry(50, errors=requests.HTTPError, timeout=30)
def http_to_file(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        shutil.copyfileobj(response.raw, f)


def read_table(table, filename):
    print('  reading %s' % filename)
    _original_table = table
    # Strip leading comments
    if table[0] in '#^':
        table = re.sub(r'^(?:[#^].*\n)+', '', table)
    # Extract platform table (for some supplementary files)
    if 'latform_table_begin' in table:
        table = re_find(r'![Pp]latform_table_begin\s+(.*?)![Pp]latform_table_end', table, re.S)

    # Try reading table
    try:
        df = pd.read_table(io.StringIO(table), index_col=0, dtype=str, engine='c')
    except Exception as e:
        cprint('Failed to parse %s: %s' % (filename, e), 'red')
        dump_error('read_table', {filename: _original_table})
        return None

    df.index = df.index.map(str)
    df.columns = df.columns.map(simplify_colname)
    # Drop columns with same name
    return df.ix[:, ~df.columns.duplicated()]


def simplify_colname(col):
    col = re_find(r'Database Entry ?\[(.*)\]$', col) or col
    return re.sub(r'\W+', '_', col).strip('_').lower()


# FTP utils

class Shared(threading.local):
    @cached_property
    def conn(self):
        return FTPHost.connect(GEO_HOST, user="anonymous", password="anonymous",
                               timeout=SOCKET_TIMEOUT)

shared = Shared()


@decorator
def ftp_retry(call):
    tries = 50
    for attempt in range(tries):
        try:
            try:
                return call()
            except ftplib.all_errors:
                # Connection could be in inconsistent state, close and forget
                shared.conn.close()
                del shared.conn
                raise
        except (ftplib.Error, socket.error, EOFError) as e:
            if error_persistent(e):
                raise
            # Reraise error on last attempt
            elif attempt + 1 == tries:
                raise
            else:
                time.sleep(20)


def error_persistent(e):
    return 'No such file or directory' in str(e)


@decorator
def ignore_no_file(call, default=None):
    try:
        return call()
    except ftplib.Error as e:
        if 'No such file or directory' in str(e):
            return default
        raise


@file_cache.cached(timeout=CACHE_TIMEOUT)
@ftp_retry
@log_errors(lambda msg: cprint(msg, 'red'), stack=False)
@ignore_no_file(default=((), ()))
def listdir(dirname):
    print(dirname)
    return shared.conn.listdir(dirname)


@file_cache.cached(timeout=CACHE_TIMEOUT)
@ftp_retry
@log_errors(lambda msg: cprint(msg, 'red'), stack=False)
def download(filename):
    print(filename)
    return shared.conn.file_proxy(filename).download_to_str()


@file_cache.cached(timeout=CACHE_TIMEOUT)
@ftp_retry
@log_errors(lambda msg: cprint(msg, 'red'), stack=False)
@ignore_no_file()
def peek_platform(filename):
    """
    Peek into gzipped platform file over ftp.
    """
    with tqdmio(desc=filename, file=sys.stdout) as pbar:
        with open_ftp_file(filename) as f:
            fd = gzip.open(pbar.wrap(f), mode='rt', encoding='latin-1')
            return extract_platform_table(fd)


from tqdm import tqdm


class tqdmio(tqdm):  # noqa
    def __init__(self, *args, **kwargs):
        kwargs.update({'unit': 'B', 'unit_scale': True, 'unit_divisor': 1024})
        return super().__init__(*args, **kwargs)

    def wrap(self, fd):
        return IOCounter(fd, self.update)


class IOCounter:
    def __init__(self, fd, update):
        self._fd = fd
        self._update = update

    def read(self, size=-1):
        data = self._fd.read(size)
        self._update(len(data))
        return data

    def __getattr__(self, attr):
        return getattr(self._fd, attr)


@contextmanager
def open_ftp_file(filename):
    ftp_conn = ftplib.FTP(GEO_HOST, timeout=SOCKET_TIMEOUT)
    ftp_conn.login()

    ftp_conn.voidcmd('TYPE I')
    bin_conn = ftp_conn.transfercmd("RETR %s" % filename)

    try:
        yield bin_conn.makefile('rb')
    finally:
        bin_conn.close()
        ftp_conn.close()


def extract_platform_table(fd):
    lines = []
    in_table = False
    for line in fd:
        if in_table:
            if line.startswith('!platform_table_end'):
                return ''.join(lines)
            lines.append(line)
        elif line.startswith('!platform_table_begin'):
            in_table = True


###

def decompress(content):
    return gzip.open(io.BytesIO(content), mode='rt', encoding='latin-1').read()


def dump_error(name, files):
    path = os.path.join(settings.BASE_DIR, '_errors', name)
    with suppress(OSError):
        os.makedirs(path)

    for filename, data in files.items():
        with open(os.path.join(path, filename), 'w') as f:
            f.write(data)
