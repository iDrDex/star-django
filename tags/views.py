import re

from funcy import filter, project, memoize, without, zipdict
from handy.db import db_execute, fetch_val
from handy.decorators import render_to

from legacy.models import Sample, Series


@render_to()
def search(request):
    q = request.GET.get('q', '')
    if q:
        qs = search_series_qs(q)
        series = paginate(request, qs, 10)
    else:
        series = None
    return {
        'columns': get_columns('series_view'),
        'series': series,
        'page': series,
    }


@render_to()
def annotate(request):
    series_id = request.GET.get('id', 1)

    # serie = fetch_serie(series_id)
    serie = Series.objects.values().get(pk=series_id)

    samples = fetch_samples(series_id)
    samples = remove_constant_fields(samples)
    columns = get_columns('sample_view')
    if samples:
        desired = set(samples[0].keys()) - {'id'}
        columns = filter(desired, columns)
    return {
        'serie': serie,
        'columns': columns,
        'samples': samples,
    }


# Data utils

def remove_constant_fields(rows):
    if len(rows) <= 1:
        return rows

    varying = {
        key
        for row in rows[1:]
        for key, value in row.items()
        if rows[0][key] != value
    }
    return [project(row, varying) for row in rows]


# Data fetching utils

HIDE_SAMPLE_FIELDS = ['sample_supplementary_file']

def search_series_qs(query_string):
    sql = """
             select {}, ts_rank_cd(doc, q) as rank
             from series_view, plainto_tsquery(%s) as q
             where doc @@ q order by rank desc
          """.format(', '.join(get_columns('series_view')))
    return SQLQuerySet(sql, (query_string,), server='legacy')


def search_series(query_string):
    return fetch_dicts(sql, (query_string,), 'legacy')


def fetch_serie(series_id):
    cols = ', '.join(get_columns('series_view'))
    return fetch_dict(
        'select ' + cols + ' from series_view where series_id = %s',
        (series_id,), 'legacy')

def fetch_samples(series_id):
    cols = get_columns('sample_view')
    cols = without(cols, *HIDE_SAMPLE_FIELDS)
    cols = ', '.join(cols)
    return fetch_dicts(
        'select ' + cols + ' from sample_view where series_id = %s',
        (series_id,), 'legacy')

@memoize
def get_columns(table):
    with db_execute('select * from %s limit 1' % table, (), 'legacy') as cursor:
        return without([col.name for col in cursor.description], 'doc')


# Pagination utility

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def paginate(request, objects, ipp):
    paginator = Paginator(objects, ipp)
    page = request.GET.get('p')
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        return paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        return paginator.page(paginator.num_pages)


# SQL

class SQLQuerySet(object):
    def __init__(self, sql, params=(), server='default'):
        self.sql = sql
        self.params = params
        self.server = server

    def count(self):
        # TODO: use sqlparse here
        count_sql = re.sub(r'select.*?from\b', 'select count(*) from', self.sql, flags=re.I | re.S)
        count_sql = re.sub(r'order by .*', '', count_sql, re.I | re.S)
        return fetch_val(count_sql, self.params, self.server)

    def __getitem__(self, k):
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."

        clauses = [self.sql]

        if isinstance(k, slice):
            if k.stop is not None:
                clauses.append('limit %d' % (k.stop - (k.start or 0)))
            if k.start is not None:
                clauses.append('offset %d' % k.start)
        else:
            clauses.append('limit 1 offset %d' % k)

        sql = ' '.join(clauses)
        return fetch_dicts(sql, self.params, self.server)


# Low level fetching tools

from operator import itemgetter

def fetch_dicts(sql, params=(), server='default'):
    with db_execute(sql, params, server) as cursor:
        field_names = map(itemgetter(0), cursor.description)
        return [zipdict(field_names, row) for row in cursor.fetchall()]

def fetch_dict(sql, params=(), server='default'):
    with db_execute(sql, params, server) as cursor:
        field_names = map(itemgetter(0), cursor.description)
        row = cursor.fetchone()
        return zipdict(field_names, row) if row else None
