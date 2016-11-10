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
from cStringIO import StringIO
from itertools import compress

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from funcy import *  # noqa
from cacheops import file_cache
from cacheops.utils import debug_cache_key
from termcolor import cprint
from ftptool import FTPHost
from gzip_reader import GzipReader
import pandas as pd
import mygene
import requests

from legacy.models import Platform, PlatformProbe


SOCKET_TIMEOUT = 20
CACHE_TIMEOUT = 4 * 24 * 60 * 60

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
        # parser.add_argument('-n', '--threads', type=int)

    def handle(self, **options):
        # Set up debugger
        if options['ipdb']:
            import sys, ipdb, traceback  # noqa

            def info(type, value, tb):
                traceback.print_exception(type, value, tb)
                print
                ipdb.pm()
            sys.excepthook = info

        platform_pks = Platform.objects.filter(datafile='').values_list('pk', flat=True) \
                                       .order_by('-pk')
        for pk in platform_pks:
            fill_probes(pk)


@print_durations
def fill_probes(platform_id):
    platform = Platform.objects.get(pk=platform_id)
    gpl_name = platform.gpl_name
    print '%s %s %s' % (platform.pk, platform.gpl_name, platform.specie)
    assert not platform.datafile
    assert platform.specie

    annot_file = '/pub/geo/DATA/annotation/platforms/%s.annot.gz' % gpl_name
    family_file = '/pub/geo/DATA/SOFT/by_platform/%s/%s_family.soft.gz' % (gpl_name, gpl_name)
    files = [annot_file, family_file]
    tables = map(peek_platform, files)
    datafile = first(compress(files, tables))  # Select first file with platform

    # TODO: check other supplementary files formats
    supplementary_dir = '/pub/geo/DATA/supplementary/platforms/%s/' % gpl_name
    _, supplementary_files = listdir(supplementary_dir)
    supplementary_files = [f for f in supplementary_files
                           if f.endswith('.txt.gz') and not re_test('\.cdf\.', f, re.I)]
    files.extend(supplementary_files)
    tables.extend(decompress(download('%s%s' % (supplementary_dir, f)))
                  for f in supplementary_files)

    if not any(tables):
        cprint('No data for %s' % gpl_name, 'red')
        platform.datafile = '<no data>'
        platform.save()
        return

    # Read tables in
    df = pd.concat(read_table(table, file) for table, file in zip(tables, files) if table)
    # del tables  # free memory

    # Try to resolve probes starting from best scopes
    for col, scopes in with_scopes(df.columns):
        probes = df.dropna(subset=[col])
        mygene_probes = mygene_fetch(platform, probes, col, scopes)

        if mygene_probes:
            with transaction.atomic():
                platform.scopes = scopes
                platform.identifier = col
                platform.datafile = datafile
                platform.save()

                PlatformProbe.objects.bulk_create([
                    PlatformProbe(platform=platform, **probe_info)
                    for probe_info in mygene_probes
                ])
                cprint('Inserted %d probes for %s' % (len(mygene_probes), gpl_name), 'green')
            break  # Stop on first match
    else:
        cprint('Nothing matched for %s' % gpl_name, 'red')
        platform.datafile = '<nothing matched>'
        platform.save()


# Ordered by priority
SCOPE_COLUMNS = (
    ('dna', ['sequence', 'platform_sequence', 'probe_sequence', 'probeseq']),
    ('entrezgene,retired', ['entrez', 'entrez_id', 'entrez_gene', 'entrez_gene_id']),
    ('ensemblgene', ['ensembl', 'ensembl_id', 'ensembl_gene', 'ensembl_gene_id', 'ensg_id']),
    ('entrezgene,retired,ensemblgene', ['gene_id']),
    ('entrezgene,retired,ensemblgene,symbol,alias', ['orf']),
    # ('unigene', []),  # Hs.12391
    ('accession', ['gb_acc', 'gene_bank_acc', 'gene_bank_accession', 'gen_bank_accession',
                   'genbank_accession', 'gb_list']),
    ('symbol,alias', ['gene_symbol']),
    ('symbol,alias,refseq,ensemblgene', ['spot_id']),
)

@collecting
def with_scopes(columns):
    for scope, fields in SCOPE_COLUMNS:
        for f in fields:
            if f in columns:
                yield f, scope


def mygene_fetch(platform, probes, col, scopes):
    """Queries mygene.info for current entrezid and sym, given an identifier."""
    if scopes == "dna":
        probes = get_dna_probes(platform, probes, col)
        col = "refMrna"
        scopes = "accession"

    _parsed_queries = probes[col].map(lambda v: re_all(r'[\w.-]+', v))
    queries_by_probe = _parsed_queries.groupby(level=0).sum()

    # Collect all possible queries to make a single request to mygene
    queries = set(icat(queries_by_probe))

    # Clean unicode for mygene
    # http://stackoverflow.com/questions/15321138/removing-unicode-u2026-like-characters
    queries = {query.decode('unicode_escape').encode('ascii', 'ignore')
               for query in queries}

    mygenes = _mygene_fetch(queries, scopes, platform.specie)

    # Form results into rows
    results = []
    warnings = []
    for probe, queries in queries_by_probe.iteritems():
        matches = distinct(keep(mygenes.get, queries))
        if len(matches) > 1:
            warnings.append((probe, queries))
        if matches:
            # Select first for now
            entrez, sym = matches[0]
            results.append({
                'probe': probe, 'mygene_sym': sym, 'mygene_entrez': entrez
            })

    # Save if more than 1 gene matched
    if warnings:
        probe_warns = []
        for probe, queries in warnings:
            resolved = [mygenes.get(q, (None, None)) for q in queries]
            explain = ''.join('    query: %s, symbol: %s, entrez: %s\n' % (q, symbol, entrez)
                              for q, (entrez, symbol) in zip(queries, resolved))
            probe_warns.append('Probe %s matches:\n%s' % (probe, explain))
        dump_error('extra_mygene_match',
                   {'%s-%s' % (platform.gpl_name, col): ''.join(probe_warns)})

    return results


@file_cache.cached(timeout=CACHE_TIMEOUT, key_func=debug_cache_key, extra=1)
def _mygene_fetch(queries, scopes, specie):
    fields = ['entrezgene', 'symbol']
    mg = mygene.MyGeneInfo()
    cprint('> Going to query %d genes in %s...' % (len(queries), scopes), 'cyan')
    data = mg.querymany(queries, scopes=scopes, fields=fields,
                        species=specie, email='suor.web@gmail.com')
    return {item['query']: (item['entrezgene'], item['symbol'])
            for item in data
            if not item.get('notfound') and 'entrezgene' in item and 'symbol' in item}


def get_dna_probes(platform, probes, col):
    from Bio import SearchIO

    blat = _ensure_blat()
    refmrna = _ensure_refmrna(platform.specie)

    # Write probes file
    probes_name = os.path.join(settings.BASE_DIR, "_files/%s.probes" % platform.gpl_name)
    with open(probes_name + ".fa", "w") as f:
        fasta = ">" + probes.index.map(str) + "\n" + probes[col]
        f.write("\n".join(fasta))

    # Match sequences
    probes_fa = probes_name + ".fa"
    probes_psl = probes_name + "-refMrna.psl"
    if not os.path.isfile(probes_psl):  # Simple caching
        cmd = """{blat}
                 {refmrna}
                 -stepSize=5
                 -repMatch=2253
                 -minScore=0
                 -minIdentity=0
                 {probes_fa} {probes_psl}""".format(**locals())
        print "BLATTING RefSeq mRNAs..."
        with print_durations('blatting %s' % platform.gpl_name):
            output = subprocess.check_call(cmd.split(), stdout=sys.stdout, stderr=sys.stderr)

    # Parse results
    print "Parsing %s psl..." % platform.gpl_name
    parser = SearchIO.parse(probes_psl, "blat-psl")
    data = []
    for result in parser:
        best_hit = max(result, key=lambda hit: max(hsp.score for hsp in hit))
        data.append((best_hit.query_id, best_hit.id))

    return pd.DataFrame(data, columns=['id', 'refMrna']).set_index('id')


def _ensure_blat():
    blat_file = os.path.join(settings.BASE_DIR, '_files/blat')
    if not os.path.isfile(blat_file):
        cprint('Downloading blat...', 'blue')
        http_to_file(LINUX_BLAT, blat_file)
        os.chmod(blat_file, 0755)
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
    _original_table = table
    # Strip leading comments
    if table[0] in '#^':
        table = re.sub(r'^(?:[#^].*\n)+', '', table)
    # Extract platform table (for some supplementary files)
    if 'latform_table_begin' in table:
        table = re_find(r'![Pp]latform_table_begin\s+(.*?)![Pp]latform_table_end', table, re.S)

    # Try reading table
    try:
        df = pd.read_table(StringIO(table), index_col=0, dtype=str, engine='c')
    except Exception as e:
        cprint('Failed to parse %s: %s' % (filename, e), 'red')
        dump_error('read_table', {filename: _original_table})
        return None

    df.index = df.index.map(str)
    df.columns = [re.sub(r'\W+', '_', col).lower() for col in df.columns]
    # Drop columns with same name
    return df.ix[:, ~df.columns.duplicated()]


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
    for attempt in xrange(tries):
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
    return 'No such file or directory' in e.message


@decorator
def ignore_no_file(call, default=None):
    try:
        return call()
    except ftplib.Error as e:
        if 'No such file or directory' in e.message:
            return default
        raise


@file_cache.cached(timeout=CACHE_TIMEOUT, key_func=debug_cache_key)
@ftp_retry
@log_errors(lambda msg: cprint(msg, 'red'), stack=False)
@ignore_no_file(default=((), ()))
def listdir(dirname):
    print dirname
    return shared.conn.listdir(dirname)


@file_cache.cached(timeout=CACHE_TIMEOUT, key_func=debug_cache_key)
@ftp_retry
@log_errors(lambda msg: cprint(msg, 'red'), stack=False)
def download(filename):
    print filename
    return shared.conn.file_proxy(filename).download_to_str()


@file_cache.cached(timeout=CACHE_TIMEOUT, key_func=debug_cache_key)
@ftp_retry
@log_errors(lambda msg: cprint(msg, 'red'), stack=False)
@ignore_no_file()
def peek_platform(filename):
    """
    Peek into gzipped platform file over ftp.
    """
    print filename
    with open_ftp_file(filename) as f:
        fd = GzipReader(f)
        return extract_platform_table(fd)


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
    return gzip.GzipFile(fileobj=StringIO(content)).read()


def dump_error(name, files):
    path = os.path.join(settings.BASE_DIR, '_errors', name)
    with suppress(OSError):
        os.makedirs(path)

    for filename, data in files.items():
        with open(os.path.join(path, filename), 'w') as f:
            f.write(data)
