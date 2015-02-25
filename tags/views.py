from funcy import filter
from handy.decorators import render_to

from legacy.models import Sample, Series


@render_to()
def index(request):
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

from funcy import project

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

from funcy import memoize, without, zipdict
from handy.db import db_execute


def fetch_serie(series_id):
    cols = ', '.join(get_columns('series_view'))
    return fetch_dict(
        'select ' + cols + ' from series_view where series_id = %s',
        (series_id,), 'legacy')

def fetch_samples(series_id):
    cols = ', '.join(get_columns('sample_view'))
    return fetch_dicts(
        'select ' + cols + ' from sample_view where series_id = %s',
        (series_id,), 'legacy')

@memoize
def get_columns(table):
    with db_execute('select * from %s limit 1' % table, (), 'legacy') as cursor:
        return without([col.name for col in cursor.description], 'doc')


from operator import itemgetter

def fetch_dicts(sql, params=(), server='default'):
    with db_execute(sql, params, server) as cursor:
        field_names = map(itemgetter(0), cursor.description)
        return [zipdict(field_names, row) for row in cursor.fetchall()]

def fetch_dict(sql, params=(), server='default'):
    with db_execute(sql, params, server) as cursor:
        field_names = map(itemgetter(0), cursor.description)
        row = cursor.fetchone()
        return zipdict(field_names, row)
