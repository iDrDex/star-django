import json
import random
from datetime import timedelta

from funcy import project, takewhile, without, distinct, merge, icat
from handy.decorators import render_to

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from core.decorators import block_POST_for_incompetent
from legacy.models import Series, Sample
from .models import Tag, ValidationJob, RawSeriesAnnotation, SeriesAnnotation
from .annotate_core import AnnotationError, save_annotation, save_validation, is_samples_concordant


@login_required
@block_POST_for_incompetent
@render_to('tags/annotate.j2')
def annotate(request):
    if request.method == 'POST':
        data = {
            'user_id': request.user.id,
            'series_id': request.POST['series_id'],
            'tag_id': request.POST['tag_id'],
            'column': request.POST['column'],
            'regex': request.POST['regex'],
            'annotations': dict(json.loads(request.POST['values'])),
        }

        try:
            with transaction.atomic():
                if RawSeriesAnnotation.objects.filter(series_id=data['series_id'],
                                                      tag_id=data['tag_id']).exists():
                    raise AnnotationError(
                        'Serie %s is already annotated with tag %s'
                        % (data['series'].gse_name, data['tag'].tag_name))

                save_annotation(data)
                messages.success(request, 'Saved annotations')
                return redirect(reverse(annotate) + '?series_id={0}'.format(data['series_id']))

        except AnnotationError as err:
            messages.error(request, unicode(err))
            return redirect(request.get_full_path())

    series_id = request.GET.get('series_id')
    if not series_id:
        raise Http404

    series = Series.objects.get(pk=series_id)
    samples, columns = fetch_annotation_data(series_id)

    done_tag_ids = SeriesAnnotation.objects.filter(series_id=series_id).values('tag_id').distinct()
    done_tags = Tag.objects.filter(id__in=done_tag_ids, is_active=True).order_by('tag_name')
    tags = Tag.objects.filter(is_active=True).exclude(id__in=done_tag_ids) \
        .order_by('tag_name').values('id', 'tag_name', 'description')

    # Get annotations statuses
    annos_qs = SeriesAnnotation.objects.filter(series=series) \
                               .values_list('tag_id', 'best_cohens_kappa')
    tags_validated = {t: k == 1 for t, k in annos_qs}

    return {
        'series': series,
        'tags': tags,
        'done_tags': done_tags,
        'tags_validated': tags_validated,
        'columns': columns,
        'samples': samples,
    }


BLIND_FIELDS = {'id', 'gsm_name', 'platform_id'}

@login_required
@block_POST_for_incompetent
@render_to('tags/annotate.j2')
def validate(request):
    if request.method == 'POST':
        # Do not check input, just crash for now

        user_id = request.user.id
        job_id = request.POST['job_id']
        try:
            with transaction.atomic():
                # Make database lock on job in queue
                job = ValidationJob.objects.select_for_update().get(id=job_id, locked_by=user_id)
                data = {
                    'user_id': user_id,
                    'column': request.POST['column'],
                    'regex': request.POST['regex'],
                    'annotations': dict(json.loads(request.POST['values'])),
                }

                # Save validation with used column and regex
                raw_annotation = save_validation(job.annotation_id, data)

                message = 'Saved {} validations for {}'.format(
                    len(data['annotations']),
                    raw_annotation.tag.tag_name)
                messages.success(request, message)

                return redirect(request.get_full_path())

        except ValidationJob.DoesNotExist:
            # TODO: fast-acquire lock if available
            messages.error(
                request,
                'Validation task timed out. Someone else could have done it.')
            return redirect(request.get_full_path())
        except AnnotationError as err:
            messages.error(request, unicode(err))
            return redirect(request.get_full_path())

    try:
        job = lock_validation_job(request.user.id)
    except ValidationJob.DoesNotExist:
        return {'TEMPLATE': 'tags/nothing_to_validate.j2'}

    canonical = job.annotation
    samples, columns = fetch_annotation_data(canonical.series_id,
                                             platform_id=canonical.platform_id, blind=BLIND_FIELDS)

    return {
        'job': job,
        'series': canonical.series,
        'tag': canonical.tag,
        'columns': columns,
        'samples': samples,
    }

@transaction.atomic
def lock_validation_job(user_id):
    # Get a job that:
    #   - not annotated by this user before,
    #   - either not locked or locked by this user or lock expired,
    #   - with active tag.
    stale_lock = timezone.now() - timedelta(minutes=30)
    lock_cond = Q(locked_by__isnull=True) | Q(locked_by=user_id) | Q(locked_on__lt=stale_lock)
    job = ValidationJob.objects.filter(lock_cond)                                \
                       .exclude(annotation__raw_annotations__created_by=user_id) \
                       .filter(annotation__tag__is_active=True)                  \
                       .select_for_update().earliest('priority')
    job.locked_by_id = user_id
    job.locked_on = timezone.now()
    job.save()

    # Remove all previous locks by this user
    ValidationJob.objects.filter(locked_by=user_id).exclude(pk=job.pk) \
        .update(locked_by=None, locked_on=None)

    return job


@login_required
@block_POST_for_incompetent
@render_to('tags/annotate.j2')
def on_demand_validate(request):
    if request.method == 'POST':
        canonical_id = request.POST['canonical_id']
        data = {
            'user_id': request.user.id,
            'column': request.POST['column'],
            'regex': request.POST['regex'],
            'annotations': dict(json.loads(request.POST['values'])),
            'on_demand': True,
        }

        # Save validation with used column and regex
        try:
            raw_annotation = save_validation(canonical_id, data)

            message = 'Saved {} validations for {}, tagged {}'.format(
                len(data['annotations']),
                raw_annotation.series.gse_name,
                raw_annotation.tag.tag_name)
            messages.success(request, message)
            return redirect(on_demand_result, raw_annotation.id)

        except AnnotationError as err:
            messages.error(request, unicode(err))
            return redirect(request.get_full_path())
    else:
        # Do not use session unless we have referer
        referer = request.META.get('HTTP_REFERER')
        if referer:
            request.session['next'] = referer

    canonical_id = request.GET.get('canonical_id')
    if canonical_id:
        canonical = get_object_or_404(SeriesAnnotation, id=canonical_id)
        series_id = canonical.series_id
    else:
        # Guess or select actual annotation
        series_id = request.GET['series_id']
        tag_id = request.GET['tag_id']

        series_annotations = SeriesAnnotation.objects.filter(series_id=series_id, tag_id=tag_id) \
                                             .select_related('series', 'platform', 'tag')
        if len(series_annotations) > 1:
            return render(request, 'tags/select_to_validate.j2',
                          {'series_annotations': series_annotations})
        else:
            canonical = series_annotations[0]

    series = Series.objects.get(pk=series_id)
    tag = canonical.tag
    samples, columns = fetch_annotation_data(series_id, canonical.platform_id, blind=BLIND_FIELDS)

    return {
        'canonical': canonical,
        'series': series,
        'tag': tag,
        'columns': columns,
        'samples': samples,
    }

@login_required
def on_demand_result(request, raw_annotation_id):
    raw_annotation = get_object_or_404(RawSeriesAnnotation, id=raw_annotation_id)
    if raw_annotation.created_by_id != request.user.id:
        raise Http404

    return render(request, 'tags/on_demand_result.j2', {
        'raw_annotation': raw_annotation,
        'next': request.session.get('next')
    })


@login_required
@render_to('tags/annotate.j2')
def competence(request):
    def same_as_canonical(raw_annotation):
        return is_samples_concordant(raw_annotation, raw_annotation.canonical)

    if request.user.is_competent:
        return redirect(validate)

    if request.method == 'POST':
        canonical_id = request.POST['canonical_id']
        data = {
            'user_id': request.user.id,
            'column': request.POST['column'],
            'regex': request.POST['regex'],
            'annotations': dict(json.loads(request.POST['values'])),
            'is_active': False,
            'by_incompetent': True,
        }

        # Save validation marking by_incompetent
        try:
            save_validation(canonical_id, data)
        except AnnotationError as err:
            messages.error(request, unicode(err))
        return redirect(competence)

    # Check how many tries and progress = number of successful tries in a row
    annotations = RawSeriesAnnotation.objects.filter(created_by=request.user, by_incompetent=True) \
                                     .order_by('-id')[:5] \
                                     .prefetch_related('sample_annotations', 'canonical',
                                                       'canonical__sample_annotations')
    first_try = len(annotations) == 0
    annotations = list(takewhile(same_as_canonical, annotations))
    progress = len(annotations)

    # 5 successful tries in a row is test pass
    if progress >= 5:
        request.user.is_competent = True
        request.user.save()
        messages.success(request, '''Congratulations! You passed competence test.<br>
                                     You can now annotate and validate series.''')
        return redirect(validate)

    # Welcome, progress and fail messages
    if progress == 0 and first_try:
        messages.info(request, '''Welcome to competence test!<br>
                                  You need to annotate 5 series in a row correctly to pass.''')
    elif progress == 0 and not first_try:
        messages.error(request, '''This one was wrong, sorry.<br>
                                   Starting from zero with fresh series.''')
    elif progress == 4:
        messages.success(request, '''You are almost there! Here is the last one.''')
    elif progress == 3:
        messages.success(request, '''Good progress, only 2 annotations left.''')
    else:
        messages.success(request, '''Correct! %d series to go.''' % (5 - progress))

    # Select canonical annotation to test against
    # NOTE: several conditions play here:
    #         - exclude annotations seen before
    #         - only use agreed upon ones (best_cohens_kappa = 1 means there are 2 concordant annos)
    #         - first 3 tries select non-controversial annotations (fleiss_kappa = 1)
    #         - exclude tags seen in this test run
    #         - last 2 tries select less obvious annotations (fleiss_kappa < 1)
    #         - 2 of all tests should use captive tags
    qs = SeriesAnnotation.objects.exclude(raw_annotations__created_by=request.user) \
                                 .filter(best_cohens_kappa=1) \
                                 .select_related('series_tag', 'series_tag__tag')

    # These conds are lifted until some test material is found
    conds = [Q(fleiss_kappa=1) if progress < 3 else Q(fleiss_kappa__lt=1)]
    seen_tags = [a.tag_id for a in annotations]
    if seen_tags:
        conds += [~Q(tag__in=seen_tags)]
    if progress == 0:
        conds += [Q(captive=False)]
    else:
        captive_left = 2 - sum(a.canonical.captive for a in annotations)
        conds += [Q(captive=random.randint(0, 5 - progress) < captive_left)]

    canonical = get_sample(qs, conds)
    if canonical is None:
        messages.error(request, '''Too many tries, we are out of test material.''')
        return redirect(validate)

    samples, columns = fetch_annotation_data(canonical.series_id, canonical.platform_id,
                                             blind=BLIND_FIELDS)

    return {
        'canonical': canonical,
        'series': canonical.series,
        'tag': canonical.tag,
        'columns': columns,
        'samples': samples,
        'progress': progress
    }

def get_sample(qs, optional_conds=()):
    """
    Get a random sample from given queryset.
    Optional conditions are lifted starting from the last one until we get some result.
    """
    while True:
        canonical = qs.filter(*optional_conds).order_by('?').first()
        if canonical is not None:
            return canonical
        elif optional_conds:
            optional_conds.pop()
        else:
            return None


# Data utils

def remove_constant_fields(rows):
    if len(rows) <= 1:
        return rows

    varying = {
        key
        for row in rows[1:]
        for key, value in row.items()
        if rows[0].get(key) != value
    }
    return [project(row, varying) for row in rows]


# Data fetching utils

def fetch_annotation_data(series_id, platform_id=None, blind=['id']):
    samples = fetch_samples(series_id, platform_id)
    samples = remove_constant_fields(samples)
    columns = without(get_samples_columns(samples), *blind)
    return samples, columns


def fetch_samples(series_id, platform_id=None):
    qs = Sample.objects.filter(series=series_id).exclude(deleted='T')
    if platform_id is not None:
        qs = qs.filter(platform=platform_id)

    return [merge(d, d['attrs']) for d in qs.values()]


def get_samples_columns(samples):
    preferred = ['id', 'description', 'characteristics_ch1', 'characteristics_ch2']
    exclude = ['attrs', 'supplementary_file', 'geo_accession']

    columns = distinct(icat(s.keys() for s in samples))
    return lift(preferred, without(columns, *exclude))


def lift(preferred, seq):
    return [col for col in preferred if col in seq] + without(seq, *preferred)
