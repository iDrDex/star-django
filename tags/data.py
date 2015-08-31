import re

from funcy import memoize, without
from handy.db import fetch_dicts, fetch_val, fetch_col, db_execute


def get_series_columns():
    preferred = ['series_id', 'series_title', 'series_summary', 'series_overall_design']
    columns = _get_columns('series_view', exclude=('id', 'doc'))
    return lift(preferred, columns)

def get_samples_columns():
    preferred = ['sample_id', 'sample_description',
                 'sample_characteristics_ch1', 'sample_characteristics_ch2']
    columns = _get_columns('sample_view', exclude=('id', 'doc', 'sample_supplementary_file'))
    return lift(preferred, columns)

@memoize
def _get_columns(table, exclude=()):
    with db_execute('select * from %s limit 1' % table, (), 'legacy') as cursor:
        columns = [col.name for col in cursor.description]
        return without(columns, *exclude)

def lift(preferred, seq):
    return [col for col in preferred if col in seq] + without(seq, *preferred)


# SQL

class SQLQuerySet(object):
    def __init__(self, sql, params=(), server='default', flat=False):
        self.sql = sql
        self.params = params
        self.server = server
        self.flat = flat

    def count(self):
        # TODO: use sqlparse here
        count_sql = re.sub(r'select.*?from\b', 'select count(*) from', self.sql, flags=re.I | re.S)
        count_sql = re.sub(r'order by .*', '', count_sql, re.I | re.S)
        return fetch_val(count_sql, self.params, self.server)

    def __iter__(self):
        return iter(self[:])

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
        if self.flat:
            return fetch_col(sql, self.params, self.server)
        else:
            return fetch_dicts(sql, self.params, self.server)

    def values_list(self, *fields, **kwargs):
        flat = kwargs.pop('flat', False)
        if kwargs:
            raise TypeError('Unexpected keyword arguments to values_list: %s' % (list(kwargs),))
        if flat and len(fields) > 1:
            raise TypeError("'flat' is not valid when values_list is called"
                            " with more than one field.")

        fields_sql = ', '.join(fields)
        sql = re.sub(r'select.*?from\b', 'select %s from' % fields_sql, self.sql, flags=re.I | re.S)
        # HACK: new fields could miss something in order by clause
        sql = re.sub(r'order by .*', '', sql, re.I | re.S)
        return SQLQuerySet(sql, self.params, self.server, flat)

    def where(self, sql, params=()):
        new_sql = re.sub(r'(where.*?)(order by|group by|$)', '\\1 and %s \\2' % sql, self.sql, re.I)
        return SQLQuerySet(new_sql, self.params + params, self.server, self.flat)
