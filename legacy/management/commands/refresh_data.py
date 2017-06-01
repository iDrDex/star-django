import re
import posixpath
import urlparse
import json
import socket
import ftplib
import threading
import time
from optparse import make_option
from Queue import PriorityQueue
from cStringIO import StringIO

from funcy import re_finder, re_iter, group_by, log_errors, cached_property, cut_prefix, memoize
from cacheops import file_cache
from cacheops.utils import debug_cache_key
from ftptool import FTPHost
from termcolor import colored, cprint
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from legacy.models import Series, Platform, Sample, SPECIES


# TODO: verbosity levels

DEFAULT_NUMBER_OF_THREADS = 20
SERIES_MATRIX_URL = urlparse.urlparse('ftp://ftp.ncbi.nih.gov/geo/series/')
SOCKET_TIMEOUT = 20
CACHE_TIMEOUT = 2 * 24 * 60 * 60

global_options = {'force': False}


class Command(BaseCommand):
    help = 'Updates series, series attributes, platforms, samples and samples attributes \n' \
           'from series matrices files hosted on GEO ftp.'
    option_list = BaseCommand.option_list + (
        make_option(
            '-n',
            action='store', type='int', dest='threads',
            default=DEFAULT_NUMBER_OF_THREADS,
            help='Number of threads'
        ),
        make_option(
            '--cond',
            action='store', dest='cond',
            help='Update series satisfying condition'
        ),
        make_option(
            '--force',
            action='store_true', dest='force',
            help='Update series even if not changed since last run'
        ),
    )

    def handle(self, **options):
        global_options.update(options)

        def gse_file(name):
            truncated = re.sub(r'\d{1,3}$', 'nnn', name)
            return '%s%s/%s/matrix/' % (SERIES_MATRIX_URL.path, truncated, name)

        queue = DataQueue()

        # Only update existing series
        qs = Series.objects.values_list('gse_name', flat=True)
        if options['cond']:
            cond = dict(re_iter(r'(\w+)=([^;]+)', options['cond']))
            qs = qs.filter(**cond)
        print colored('Going to update %d series...' % len(qs), attrs=['bold'])
        queue.put_dirs(gse_file(name) for name in qs)

        # Launch worker threads
        for index in range(options['threads']):
            thread = DataRefreshThread(index, queue)
            thread.start()

        # Use this construction to be able to Ctrl-C
        time.sleep(5)
        while not queue.empty():
            time.sleep(1)
        # Need to join since queue.empty() is vulnerable to races
        queue.join()

        # TODO: refresh materialized views


def load_data(header):
    print colored('Found %d data lines' % len(header), 'cyan')
    line_groups = group_by(r'^!([^_]+)_', header)

    # Load series
    series_df = get_df_from_lines(line_groups['Series'], 'Series')
    assert len(series_df.index) == 1
    gse_name = series_df['series_geo_accession'][0]

    # Check if series updated
    try:
        old_last_update = Series.objects.get(gse_name=gse_name).attrs.get('last_update_date')
    except Series.DoesNotExist:
        old_last_update = None
    new_last_update = series_df['series_last_update_date'][0]
    if new_last_update == old_last_update and not global_options['force']:
        print colored('%s not changed since %s' % (gse_name, old_last_update), 'yellow')
        return
    else:
        print colored('%s updated %s -> %s' % (gse_name, old_last_update, new_last_update), 'green')

    # Load samples
    samples_df = get_df_from_lines(line_groups['Sample'], 'Sample')
    samples_df['gsm_name'] = samples_df.sample_geo_accession
    samples_df = samples_df.set_index('gsm_name')

    insert_or_update_data(series_df, samples_df)


@transaction.atomic
def insert_or_update_data(series_df, samples_df):
    gse_name = series_df['series_geo_accession'][0]

    # Create series and its attributes
    attrs = {cut_prefix(name, 'series_'): uni_cat(series_df[name]) for name in series_df.columns}
    series, created = Series.objects.update_or_create(gse_name=gse_name, defaults={'attrs': attrs})

    # Create platform
    gpls = samples_df['sample_platform_id'].unique()
    assert len(gpls) == 1
    gpl_name = gpls[0]
    print "  %s" % gpl_name
    specie = SPECIES.get(attrs['platform_taxid'], 'taxid-%s' % attrs['platform_taxid'])
    platform, _ = Platform.objects.get_or_create(gpl_name=gpl_name, defaults={'specie': specie})

    # If updating check if some samples no longer present,
    # mark disappeared samples as deleted.
    if not created:
        old_samples = Sample.objects.filter(series=series, platform=platform) \
                                    .filter(Q(deleted=None) | Q(deleted='F')) \
                                    .values_list('gsm_name', flat=True)
        dead_samples = set(old_samples) - set(samples_df.index)
        if dead_samples:
            # Use lame boolean-like 'T' cause sharing db with web2py
            Sample.objects.filter(series=series, platform=platform, gsm_name__in=dead_samples) \
                          .update(deleted='T')
            print colored('  marked %d samples as deleted' % len(dead_samples), 'red')

    # Create/update samples and their attributes
    for gsm_name in samples_df.index:
        attrs = {cut_prefix(name, 'sample_'): value.strip()
                 for name, value in samples_df.ix[gsm_name].to_dict().items()}
        Sample.objects.update_or_create(
            gsm_name=gsm_name, series=series, platform=platform, deleted=None,
            defaults={'attrs': attrs})

    action = 'inserted' if created else 'updated'
    print colored('  %s %s, %d samples' % (action, gse_name, len(samples_df)),
                  'green', attrs=['bold'])


def uni_cat(fields, fieldSep="|\n|"):
    """Unique concatenation of """
    return fieldSep.join(fields.astype(str).unique())


def get_clean_columns(columns):
    return [re.sub(r'\W+', '_', col[1:]).lower() for col in columns]


def get_df_from_lines(lines, entity):
    stream = StringIO(''.join(lines))

    index_col = '!%s_title' % entity
    df = pd.io.parsers.read_table(stream) \
        .dropna(how='all')  \
        .groupby(index_col) \
        .aggregate(uni_cat) \
        .T
    df.index.name = index_col
    df = df.reset_index()  # may want to store title
    df.columns = get_clean_columns(df.columns)
    return df


def check_dir(dirname):
    return re.search(r'^(GSE|matrix)', dirname)


find_value = re_finder(r'"(.*)"')

def check_line(line, acc):
    # Start of data, end of header. Stop and pass header
    if line.startswith('!series_matrix_table_begin'):
        return True

    # If serie is known then ignore filters below
    if line.startswith('!Series_geo_accession') and find_value(line) in known_gses():
        acc['known'] = True
    if acc.get('known'):
        return None

    # Only fetch this type of studies
    if line.startswith('!Series_type') and find_value(line) != "Expression profiling by array":
        return False

    # Only fetch human studies
    if line.startswith('!Series_sample_taxid') and find_value(line) not in SPECIES:
        return False

@memoize
def known_gses():
    return set(Series.objects.values_list('gse_name', flat=True))


# Job/data managing utilities

class DataQueue(PriorityQueue):
    def put_dirs(self, dirs):
        for d in dirs:
            self.put((100, 'dir', d))

    def put_files(self, files):
        for f in files:
            self.put((90, 'file', f))

    def put_header(self, header):
        self.put((80, 'header', header))


class DataRefreshThread(threading.Thread):
    def __init__(self, index, queue):
        threading.Thread.__init__(self)
        self.index = index
        self.queue = queue
        self.daemon = True

    @cached_property
    def conn(self):
        return FTPHost.connect(SERIES_MATRIX_URL.netloc,
                               user="anonymous", password="anonymous", timeout=SOCKET_TIMEOUT)

    def run(self):
        while True:
            try:
                _, task, arg = item = self.queue.get()
                task = 'do_' + task

                try:
                    if not hasattr(self, task):
                        raise NameError('No task %s defined' % task)
                    getattr(self, task)(arg)
                except (ftplib.Error, socket.error, EOFError) as e:
                    # Could happen in a number of cases:
                    #   - connection timed out or broke,
                    #   - ftp connections exceeded
                    #   - directory structure changed and we get directory or file not found
                    # Trying to reschedule
                    if not error_persistent(e):
                        self.queue.put(item)
                        time.sleep(60)
                except Exception as e:
                    self.queue.queue = []
                    import traceback; traceback.print_exc()  # flake8: noqa
                    import ipdb; ipdb.set_trace()            # flake8: noqa
                    import os
                    os._exit(1)
            finally:
                self.queue.task_done()

    @log_errors(lambda msg: cprint(msg, 'red'), stack=False)
    def do_dir(self, dirname):
        @file_cache.cached(timeout=CACHE_TIMEOUT, key_func=debug_cache_key)
        def listdir(d):
            return self.conn.listdir(d)

        print dirname
        try:
            dirs, files = listdir(dirname)
        except ftplib.all_errors:
            # Connection could be in inconsistent state, close and forget
            self.conn.close()
            del self.conn
            raise

        self.queue.put_files(posixpath.join(dirname, f) for f in files)
        self.queue.put_dirs(posixpath.join(dirname, d) for d in dirs if check_dir(d))

    @log_errors(lambda msg: cprint(msg, 'red'), stack=False)
    def do_file(self, filename):
        print filename
        header = peek_matrix(SERIES_MATRIX_URL.netloc, filename)
        if header:
            print "  %s is interesting" % filename
            self.queue.put_header(header)
        else:
            print "  %s is a miss" % filename

    def do_header(self, header):
        load_data(header)


# Low level utilities

from gzip_reader import GzipReader

@file_cache.cached(timeout=CACHE_TIMEOUT, key_func=debug_cache_key)
def peek_matrix(host, filename):
    """
    Peek into gzipped serie matrix file over ftp,
    returns its header if it satisfies check_line() conditions.
    """
    ftp_conn = ftplib.FTP(host, timeout=SOCKET_TIMEOUT)
    ftp_conn.login()

    ftp_conn.voidcmd('TYPE I')
    bin_conn = ftp_conn.transfercmd("RETR %s" % filename)
    fd = GzipReader(bin_conn.makefile('rb'))

    try:
        lines = []
        acc = {}
        for line in fd:
            lines.append(line)
            check = check_line(line, acc)
            if check is not None:
                if check:
                    return lines
                break
    finally:
        bin_conn.close()
        ftp_conn.close()


def error_persistent(e):
    return isinstance(e, ftplib.error_temp) and 'No such file or directory' in e.message
