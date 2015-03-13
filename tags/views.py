import re
import json
from datetime import timedelta

from funcy import filter, project, memoize, without, group_by, first
from handy.db import db_execute, fetch_val, fetch_dict, fetch_dicts
from handy.decorators import render_to, paginate

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils import timezone

from legacy.models import Sample, Series, Tag, SeriesTag, SampleTag
from tags.models import ValidationJob, SerieValidation, SampleValidation


@render_to()
@paginate('series', 10)
def search(request):
    request.session['last_search'] = request.get_full_path()
    q = request.GET.get('q')
    return {
        'columns': get_series_columns(),
        'series': search_series_qs(q) if q else None,
    }


@render_to()
def annotate(request):
    if request.method == 'POST':
        if not request.user_data.get('id'):
            return redirect(settings.LEGACY_APP_URL + '/default/user/login')

        if save_annotation(request):
            return redirect(request.session.get('last_search', '/'))
        else:
            return redirect(request.get_full_path())

    series_id = request.GET.get('series_id')
    if not series_id:
        raise Http404

    serie = Series.objects.values().get(pk=series_id)
    samples, columns = fetch_annotation_data(series_id)

    done_tag_ids = SeriesTag.objects.filter(series_id=series_id).values('tag_id')
    done_tags = Tag.objects.filter(id__in=done_tag_ids).order_by('tag_name')
    tags = Tag.objects.filter(is_active='T').exclude(id__in=done_tag_ids) \
        .order_by('tag_name').values('id', 'tag_name')

    return {
        'done_tags': done_tags,
        'tags': tags,
        'serie': serie,
        'columns': columns,
        'samples': samples,
    }


@transaction.atomic('legacy')
def save_annotation(request):
    user_id = request.user_data['id']

    # Do not check input, just crash for now
    series_id = request.POST['series_id']
    tag_id = request.POST['tag_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    # Group samples by platform
    sample_to_platform = dict(Sample.objects.filter(id__in=values).values_list('id', 'platform_id'))
    groups = group_by(lambda (id, _): sample_to_platform[id], values.items())

    old_annotation = first(SeriesTag.objects.filter(series_id=series_id, tag_id=tag_id))
    if old_annotation:
        messages.error(request, 'Serie %s is already annotated with tag %s'
                       % (old_annotation.series.gse_name, old_annotation.tag.tag_name))
        return False

    # Save all annotations and used regexes
    for platform_id, annotations in groups.items():
        # Do not allow for same user to annotate same serie twice
        series_tag, created = SeriesTag.objects.get_or_create(
            series_id=series_id, platform_id=platform_id, tag_id=tag_id, created_by_id=user_id,
            defaults=dict(header=column, regex=regex, modified_by_id=user_id)
        )

        # Create all sample tags
        SampleTag.objects.bulk_create([
            SampleTag(sample_id=sample_id, series_tag=series_tag, annotation=annotation,
                      created_by_id=user_id, modified_by_id=user_id)
            for sample_id, annotation in annotations
        ])

        # Create validation job
        ValidationJob.objects.create(series_tag=series_tag)

    return True


BLIND_FIELDS = {'id', 'sample_id', 'sample_geo_accession', 'sample_platform_id', 'platform_id'}

@render_to('tags/annotate.j2')
def validate(request):
    # TODO: write @login_required
    if not request.user_data.get('id'):
        return redirect(settings.LEGACY_APP_URL + '/default/user/login')

    if request.method == 'POST':
        save_validation(request)
        return redirect(request.get_full_path())

    try:
        job = lock_validation_job(request.user_data['id'])
    except ValidationJob.DoesNotExist:
        return {'TEMPLATE': 'tags/nothing_to_validate.j2'}

    serie = job.series_tag.series
    tag = job.series_tag.tag
    samples, columns = fetch_annotation_data(job.series_tag.series_id, blind=BLIND_FIELDS)

    return {
        'job': job,
        'serie': serie,
        'tag': tag,
        'columns': columns,
        'samples': samples,
    }

@transaction.atomic('legacy')
def save_validation(request):
    # Do not check input, just crash for now
    user_id = request.user_data['id']
    job_id = request.POST['job_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    # Make database lock on job in queue
    try:
        job = ValidationJob.objects.select_for_update().get(id=job_id, locked_by=user_id)
    except ValidationJob.DoesNotExist:
        # TODO: fast-acquire lock if available
        messages.error(request, 'Validation task timed out. Someone else could have done it.')
        return

    # Save validation with used column and regex
    st = job.series_tag
    serie_validation, created = SerieValidation.objects.get_or_create(
        series_tag_id=st.id, created_by_id=user_id,
        defaults=dict(
            column=column, regex=regex,
            series_id=st.series_id, platform_id=st.platform_id, tag_id=st.tag_id
        )
    )
    # Do not allow user validate same serie, same platform for same tag twice
    if not created:
        messages.error(request, 'You had already validated this annotation')
        return

    # Create all sample validations
    SampleValidation.objects.bulk_create([
        SampleValidation(sample_id=sample_id, serie_validation=serie_validation,
                         annotation=annotation, created_by_id=user_id)
        for sample_id, annotation in values.items()
    ])

    # Remove validation job from queue
    job.delete()

    message = 'Saved {} validations for {}'.format(len(values), serie_validation.tag.tag_name)
    messages.success(request, message)


@transaction.atomic('legacy')
def lock_validation_job(user_id):
    # Get a job that:
    #   - not authored by this user,
    #   - either not locked or locked by this user or lock expired,
    #   - not validated by this user.
    stale_lock = timezone.now() - timedelta(minutes=30)
    lock_cond = Q(locked_by__isnull=True) | Q(locked_by=user_id) | Q(locked_on__lt=stale_lock)
    job = ValidationJob.objects.filter(lock_cond)                            \
                       .exclude(series_tag__created_by=user_id)              \
                       .exclude(series_tag__validations__created_by=user_id) \
                       .select_for_update().earliest('?')
    job.locked_by_id = user_id
    job.locked_on = timezone.now()
    job.save()

    # Remove all previous locks by this user
    ValidationJob.objects.filter(locked_by=user_id).exclude(pk=job.pk) \
        .update(locked_by=None, locked_on=None)

    return job


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

def fetch_annotation_data(series_id, blind={'id'}):
    samples = fetch_samples(series_id)
    samples = remove_constant_fields(samples)
    columns = get_samples_columns()
    if samples:
        desired = set(samples[0].keys()) - blind
        columns = filter(desired, columns)

    return samples, columns


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
