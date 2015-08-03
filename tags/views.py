import re
import json
from datetime import timedelta
from collections import defaultdict
from operator import itemgetter

from funcy import *  # noqa
from handy.db import db_execute, fetch_val, fetch_dict, fetch_dicts, fetch_col
from handy.decorators import render_to, paginate

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from legacy.models import Sample, Tag, SeriesTag, SampleTag
from core.tasks import update_stats, update_graph
from core.utils import login_required
from .models import ValidationJob, SerieValidation, SampleValidation
from .tasks import calc_validation_stats


@render_to()
@paginate('series', 10)
def search(request):
    q = request.GET.get('q')
    exclude_tags = request.GET.getlist('exclude_tags')
    serie_tags, tag_series = series_tags_data()

    if q:
        qs = search_series_qs(q)
        series_ids = qs.values_list('series_id', flat=True)
        tags = distinct(imapcat(serie_tags, series_ids), key=itemgetter('id'))

        if exclude_tags:
            exclude_series = join(tag_series[int(t)] for t in exclude_tags)
            qs = qs.where('series_id not in (%s)' % str_join(',', exclude_series))
    else:
        qs = None
        tags = None

    return {
        'columns': get_series_columns(),
        'series': qs,
        'tags': tags,
        'serie_tags': serie_tags,
    }


@login_required
@render_to()
def annotate(request):
    if request.method == 'POST':
        return save_annotation(request)

    series_id = request.GET.get('series_id')
    if not series_id:
        raise Http404

    serie = fetch_serie(series_id)
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


def save_annotation(request):
    user_id = request.user_data['id']

    # Do not check input, just crash for now
    series_id = request.POST['series_id']
    tag_id = request.POST['tag_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    with transaction.atomic('legacy'):
        # Group samples by platform
        sample_to_platform = dict(Sample.objects.filter(id__in=values)
                                        .values_list('id', 'platform_id'))
        groups = group_by(lambda (id, _): sample_to_platform[id], values.items())

        old_annotation = first(SeriesTag.objects.filter(series_id=series_id, tag_id=tag_id))
        if old_annotation:
            messages.error(request, 'Serie %s is already annotated with tag %s'
                           % (old_annotation.series.gse_name, old_annotation.tag.tag_name))
            return redirect(request.get_full_path())

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

    messages.success(request, 'Saved annotations')

    update_stats.delay()
    update_graph.delay()

    return redirect(reverse(annotate) + '?series_id=' + series_id)


BLIND_FIELDS = {'id', 'sample_id', 'sample_geo_accession', 'sample_platform_id', 'platform_id'}

@login_required
@render_to('tags/annotate.j2')
def validate(request):
    if request.method == 'POST':
        return save_validation(request)

    try:
        job = lock_validation_job(request.user_data['id'])
    except ValidationJob.DoesNotExist:
        return {'TEMPLATE': 'tags/nothing_to_validate.j2'}

    tag = job.series_tag.tag
    samples, columns = fetch_annotation_data(
        job.series_tag.series_id, platform_id=job.series_tag.platform_id, blind=BLIND_FIELDS)

    return {
        'job': job,
        'serie': fetch_serie(job.series_tag.series_id),
        'tag': tag,
        'columns': columns,
        'samples': samples,
    }

def save_validation(request):
    # Do not check input, just crash for now
    user_id = request.user_data['id']
    job_id = request.POST['job_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    with transaction.atomic('legacy'):
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
            return redirect(request.get_full_path())

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

    calc_validation_stats.delay(serie_validation.pk)
    update_stats.delay()
    update_graph.delay()

    return redirect(request.get_full_path())


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
                       .select_for_update().earliest('priority')
    job.locked_by_id = user_id
    job.locked_on = timezone.now()
    job.save()

    # Remove all previous locks by this user
    ValidationJob.objects.filter(locked_by=user_id).exclude(pk=job.pk) \
        .update(locked_by=None, locked_on=None)

    return job


@login_required
@render_to('tags/annotate.j2')
def on_demand_validate(request):
    if request.method == 'POST':
        return save_on_demand_validation(request)

    series_tag_id = request.GET.get('series_tag_id')
    if series_tag_id:
        series_tag = get_object_or_404(SeriesTag, id=series_tag_id)
        series_id = series_tag.series_id
    else:
        # Guess or select actual annotation
        series_id = request.GET['series_id']
        tag_id = request.GET['tag_id']

        series_tags = SeriesTag.objects.filter(series_id=series_id, tag_id=tag_id) \
                               .select_related('series', 'platform', 'tag')
        if len(series_tags) > 1:
            return render(request, 'tags/select_to_validate.j2', {'series_tags': series_tags})
        else:
            series_tag = series_tags[0]

    serie = fetch_serie(series_id)
    tag = series_tag.tag
    samples, columns = fetch_annotation_data(series_id, series_tag.platform_id)

    return {
        'series_tag': series_tag,
        'serie': serie,
        'tag': tag,
        'columns': columns,
        'samples': samples,
    }

def save_on_demand_validation(request):
    user_id = request.user_data['id']
    series_tag_id = request.POST['series_tag_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    with transaction.atomic('legacy'):
        # Save validation with used column and regex
        st = SeriesTag.objects.get(pk=series_tag_id)
        serie_validation = SerieValidation.objects.create(
            series_tag_id=st.id, created_by_id=user_id,
            column=column, regex=regex,
            series_id=st.series_id, platform_id=st.platform_id, tag_id=st.tag_id,
            on_demand=True
        )

        # Create all sample validations
        SampleValidation.objects.bulk_create([
            SampleValidation(sample_id=sample_id, serie_validation=serie_validation,
                             annotation=annotation, created_by_id=user_id)
            for sample_id, annotation in values.items()
        ])

    message = 'Saved {} validations for {}, tagged {}'.format(
        len(values), st.series.gse_name, st.tag.tag_name)
    messages.success(request, message)

    calc_validation_stats.delay(serie_validation.pk)
    update_stats.delay()
    update_graph.delay()

    return redirect(on_demand_result, serie_validation.id)

@login_required
def on_demand_result(request, serie_validation_id):
    serie_validation = get_object_or_404(SerieValidation, id=serie_validation_id)
    if serie_validation.created_by_id != request.user_data['id']:
        raise Http404

    if request.is_ajax():
        data = select_keys(r'kappa', serie_validation.__dict__)
        return JsonResponse(data)

    return render(request, 'tags/on_demand_result.j2', {'serie_validation': serie_validation})


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

def fetch_annotation_data(series_id, platform_id=None, blind={'id'}):
    samples = fetch_samples(series_id, platform_id=platform_id)
    samples = remove_constant_fields(samples)
    columns = get_samples_columns()
    if samples:
        desired = set(samples[0].keys()) - blind
        columns = filter(desired, columns)

    return samples, columns


def search_series_qs(query_string):
    sql = """
             select S.gse_name, {}, ts_rank_cd(doc, q) as rank
             from series_view SV join series S on (SV.series_id = S.id)
             , plainto_tsquery('english', %s) as q
             where doc @@ q order by rank desc
          """.format(', '.join(get_series_columns()))
    return SQLQuerySet(sql, (query_string,), server='legacy')


def series_tags_data():
    pairs = SeriesTag.objects.values_list('series_id', 'tag_id', 'tag__tag_name').distinct()

    serie_tags = defaultdict(list)
    tag_series = defaultdict(set)
    for serie_id, tag_id, tag_name in pairs:
        serie_tags[serie_id].append({'id': tag_id, 'name': tag_name})
        tag_series[tag_id].add(serie_id)

    return serie_tags, tag_series


def fetch_serie(series_id):
    cols = ', '.join(get_series_columns())
    return fetch_dict(
        '''select ''' + cols + ''', S.gse_name from series_view V
            join series S on (V.series_id = S.id)
            where V.series_id = %s''',
        (series_id,), 'legacy')

def fetch_samples(series_id, platform_id=None):
    cols = ', '.join(get_samples_columns())
    sql = 'select ' + cols + ' from sample_view where series_id = %s'
    params = (series_id,)
    if platform_id:
        sql += ' and platform_id = %s'
        params += (platform_id,)
    return fetch_dicts(sql, params, 'legacy')


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
