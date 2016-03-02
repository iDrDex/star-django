import json
from datetime import timedelta

from funcy import group_by, first, project, select_keys, filter
from handy.decorators import render_to
from handy.db import fetch_dict, fetch_dicts

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from core.tasks import update_dashboard
from legacy.models import Sample
from tags.models import Tag, SeriesTag, SampleTag
from .models import ValidationJob, SerieValidation, SampleValidation, SerieAnnotation
from .tasks import validation_workflow
from .data import get_series_columns, get_samples_columns


@login_required
@render_to('tags/annotate.j2')
def annotate(request):
    if request.method == 'POST':
        return save_annotation(request)

    series_id = request.GET.get('series_id')
    if not series_id:
        raise Http404

    serie = fetch_serie(series_id)
    samples, columns = fetch_annotation_data(series_id)

    done_tag_ids = SeriesTag.objects.filter(series_id=series_id).values('tag_id')
    done_tags = Tag.objects.filter(id__in=done_tag_ids, is_active=True).order_by('tag_name')
    tags = Tag.objects.filter(is_active=True).exclude(id__in=done_tag_ids) \
        .order_by('tag_name').values('id', 'tag_name')

    return {
        'done_tags': done_tags,
        'tags': tags,
        'serie': serie,
        'columns': columns,
        'samples': samples,
    }


def save_annotation(request):
    user_id = request.user.id

    # Do not check input, just crash for now
    series_id = request.POST['series_id']
    tag_id = request.POST['tag_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    with transaction.atomic():
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

            # TODO: check if this can result in sample tags doubling
            # Create all sample tags
            sample_tags = SampleTag.objects.bulk_create([
                SampleTag(sample_id=sample_id, series_tag=series_tag, annotation=annotation,
                          created_by_id=user_id, modified_by_id=user_id)
                for sample_id, annotation in annotations
            ])

            # Create validation job
            ValidationJob.objects.create(series_tag=series_tag)

            # Create canonical annotation
            sa = SerieAnnotation.create_from_series_tag(series_tag)
            sa.fill_samples(sample_tags)

    messages.success(request, 'Saved annotations')

    update_dashboard.delay()

    return redirect(reverse(annotate) + '?series_id=' + series_id)


BLIND_FIELDS = {'id', 'sample_id', 'sample_geo_accession', 'sample_platform_id', 'platform_id'}

@login_required
@render_to('tags/annotate.j2')
def validate(request):
    if request.method == 'POST':
        return save_validation(request)

    try:
        job = lock_validation_job(request.user.id)
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
    user_id = request.user.id
    job_id = request.POST['job_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    with transaction.atomic():
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

    validation_workflow.delay(serie_validation.pk)

    return redirect(request.get_full_path())


@transaction.atomic
def lock_validation_job(user_id):
    # Get a job that:
    #   - not authored by this user,
    #   - either not locked or locked by this user or lock expired,
    #   - not validated by this user,
    #   - with non-deleted tag.
    stale_lock = timezone.now() - timedelta(minutes=30)
    lock_cond = Q(locked_by__isnull=True) | Q(locked_by=user_id) | Q(locked_on__lt=stale_lock)
    job = ValidationJob.objects.filter(lock_cond)                            \
                       .exclude(series_tag__created_by=user_id)              \
                       .exclude(series_tag__validations__created_by=user_id) \
                       .filter(series_tag__tag__is_active=True)              \
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
    user_id = request.user.id
    series_tag_id = request.POST['series_tag_id']
    column = request.POST['column']
    regex = request.POST['regex']
    values = dict(json.loads(request.POST['values']))

    with transaction.atomic():
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

    validation_workflow.delay(serie_validation.pk)

    return redirect(on_demand_result, serie_validation.id)

@login_required
def on_demand_result(request, serie_validation_id):
    serie_validation = get_object_or_404(SerieValidation, id=serie_validation_id)
    if serie_validation.created_by_id != request.user.id:
        raise Http404

    if 'json' in request.GET:
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


def fetch_serie(series_id):
    cols = ', '.join(get_series_columns())
    return fetch_dict(
        '''select ''' + cols + ''', S.gse_name from series_view V
            join series S on (V.series_id = S.id)
            where V.series_id = %s''',
        (series_id,)
    )


def fetch_samples(series_id, platform_id=None):
    cols = ', '.join(get_samples_columns())
    sql = 'select ' + cols + ' from sample_view where series_id = %s'
    params = (series_id,)
    if platform_id:
        sql += ' and platform_id = %s'
        params += (platform_id,)
    return fetch_dicts(sql, params)
