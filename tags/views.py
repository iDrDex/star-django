import re
import json

from funcy import filter, project, memoize, without, zipdict, group_by
from handy.db import db_execute, fetch_val
from handy.decorators import render_to

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect

from legacy.models import Sample, Series, Tag, SeriesTag, SampleTag


@render_to()
def search(request):
    request.session['last_search'] = request.get_full_path()
    q = request.GET.get('q', '')
    if q:
        qs = search_series_qs(q)
        series = paginate(request, qs, 10)
    else:
        series = None
    return {
        'columns': get_series_columns(),
        'series': series,
        'page': series,
    }


@render_to()
def annotate(request):
    if not request.user_data.get('id'):
        return redirect(settings.LEGACY_APP_URL + '/default/user/login')

    if request.method == 'POST':
        save_annotation(request)
        return redirect(request.session.get('last_search', '/'))
        # return redirect(request.get_full_path())

    series_id = request.GET.get('id')
    if not series_id:
        raise Http404

    serie = Series.objects.values().get(pk=series_id)

    samples = fetch_samples(series_id)
    samples = remove_constant_fields(samples)
    columns = get_samples_columns()
    if samples:
        desired = set(samples[0].keys()) - {'id'}
        columns = filter(desired, columns)

    return {
        'tags': Tag.objects.filter(is_active='T').order_by('tag_name').values('id', 'tag_name'),
        'serie': serie,
        'columns': columns,
        'samples': samples,
    }

@transaction.atomic
def save_annotation(request):
    user_id = request.user_data['id']

    # Do not check input, just crash for now
    series_id = request.POST['id']
    tag_id = request.POST['tag']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    # Group samples by platform
    sample_to_platform = dict(Sample.objects.filter(id__in=values).values_list('id', 'platform_id'))
    groups = group_by(lambda (id, _): sample_to_platform[id], values.items())

    # Save all annotations and used regexes
    for platform_id, annotations in groups.items():
        # Do not allow for same user to annotate same serie twice
        series_tag, created = SeriesTag.objects.get_or_create(
            series_id=series_id, platform_id=platform_id, tag_id=tag_id, created_by_id=user_id,
            defaults=dict(header=column, regex=regex, modified_by_id=user_id)
        )
        if not created:
            SampleTag.objects.filter(series_tag=series_tag).delete()

        # Create all sample tags
        SampleTag.objects.bulk_create([
            SampleTag(sample_id=sample_id, series_tag=series_tag, annotation=annotation,
                      created_by_id=user_id, modified_by_id=user_id)
            for sample_id, annotation in annotations
        ])


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

def search_series_qs(query_string):
    sql = """
             select {}, ts_rank_cd(doc, q) as rank
             from series_view, plainto_tsquery('english', %s) as q
             where doc @@ q order by rank desc
          """.format(', '.join(get_series_columns()))
    return SQLQuerySet(sql, (query_string,), server='legacy')

def fetch_serie(series_id):
    cols = ', '.join(get_series_columns())
    return fetch_dict(
        'select ' + cols + ' from series_view where series_id = %s',
        (series_id,), 'legacy')

def fetch_samples(series_id):
    cols = ', '.join(get_samples_columns())
    return fetch_dicts(
        'select ' + cols + ' from sample_view where series_id = %s',
        (series_id,), 'legacy')


def get_series_columns():
    return _get_columns('series_view', exclude=('id', 'doc'))

def get_samples_columns():
    return _get_columns('sample_view', exclude=('id', 'doc', 'sample_supplementary_file'))

@memoize
def _get_columns(table, exclude=()):
    with db_execute('select * from %s limit 1' % table, (), 'legacy') as cursor:
        columns = [col.name for col in cursor.description]
        return without(columns, *exclude)


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
