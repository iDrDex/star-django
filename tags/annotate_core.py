from collections import defaultdict
import math
from operator import attrgetter

from funcy import group_by, project, first, lcat, ldistinct, chain
from django.db import transaction
import numpy as np
from statsmodels.stats.inter_rater import fleiss_kappa, cohens_kappa

from tags.models import ValidationJob, SeriesAnnotation, RawSeriesAnnotation, UserStats
from legacy.models import Sample


class AnnotationError(Exception):
    pass


@transaction.atomic
def save_annotation(data):
    user_id = data['user_id']
    annotations = data['annotations']

    sample_to_platform = dict(Sample.objects.filter(id__in=annotations)
                                    .values_list('id', 'platform_id'))
    groups = group_by(lambda pair: sample_to_platform[pair[0]], annotations.items())

    for platform_id, annotations in groups.items():
        canonical = SeriesAnnotation.objects.create(
            platform_id=platform_id,
            annotations=1,
            authors=1,
            **project(data, ['series_id', 'tag_id', 'column', 'regex'])
        )
        canonical.fill_samples(annotations)

        raw_annotation = RawSeriesAnnotation.objects.create(
            canonical=canonical,
            platform_id=platform_id,
            created_by_id=user_id,
            **project(data, ['series_id', 'tag_id', 'column', 'regex', 'note', 'from_api'])
        )
        raw_annotation.fill_samples(annotations)

        ValidationJob.objects.create(annotation=canonical)


@transaction.atomic
def save_validation(canonical_id, data):
    user_id = data['user_id']
    annotations = data['annotations']
    canonical = SeriesAnnotation.objects.select_for_update().get(id=canonical_id)

    if not data.get('on_demand') and canonical.raw_annotations.filter(created_by=user_id).exists():
        raise AnnotationError('You had already annotated this series/platform/tag')

    raw_annotation = RawSeriesAnnotation.objects.create(
        canonical=canonical,
        series_id=canonical.series_id,
        platform_id=canonical.platform_id,
        tag_id=canonical.tag_id,
        created_by_id=user_id,
        **project(data, ['column', 'regex', 'note', 'from_api',
                         'is_active', 'on_demand', 'by_incompetent'])
    )
    raw_annotation.fill_samples(annotations.items())

    ValidationJob.objects.filter(annotation=canonical).delete()

    calc_validation_stats(raw_annotation)
    if raw_annotation.is_active:
        update_canonical(canonical.pk)
    if canonical.best_cohens_kappa != 1:
        reschedule_validation(canonical)

    return raw_annotation


@transaction.atomic
def calc_validation_stats(raw_annotation):
    raw_samples = raw_annotation.sample_annotations.all()
    canonical = raw_annotation.canonical
    canonical_samples = canonical.sample_annotations.all()

    # Compare to other annotations
    earlier_annotations = canonical.raw_annotations.prefetch_related('sample_annotations') \
        .filter(pk__lt=raw_annotation.pk, is_active=True).order_by('pk')

    # If sample set changed than all earlier annotations should be disabled
    raw_sample_ids = {r.sample_id for r in raw_samples}
    if {s.sample_id for s in canonical_samples} != raw_sample_ids:
        for e in earlier_annotations:
            if {s.sample_id for s in e.sample_annotations.all()} != raw_sample_ids:
                e.obsolete = True
                e.is_active = False
                e.save()
        # Force refetch
        earlier_annotations = earlier_annotations._clone()

    # Find matching earlier annotation
    if earlier_annotations:
        raw_annotation.agrees_with = first(
            a for a in earlier_annotations
            if a.created_by_id != raw_annotation.created_by_id
            and is_samples_concordant(a, raw_annotation)
        )
        raw_annotation.best_kappa = max(_cohens_kappa(raw_samples, a.sample_annotations.all())
                                        for a in earlier_annotations)

    # Fill in user stats and earnings unless already did
    if not raw_annotation.accounted_for and raw_annotation.is_active \
            and not raw_annotation.on_demand:
        update_user_stats(raw_annotation, len(raw_samples))  # including payment ones
        raw_annotation.accounted_for = True

    raw_annotation.save()


def is_samples_concordant(anno1, anno2):
    ref1 = {s.sample_id: s.annotation for s in anno1.sample_annotations.all()}
    ref2 = {s.sample_id: s.annotation for s in anno2.sample_annotations.all()}
    return ref1 == ref2


def update_user_stats(raw_annotation, samples):
    def lock_author_stats(work):
        stats, _ = UserStats.objects.select_for_update().get_or_create(user_id=work.created_by_id)
        return stats

    # Update validating user stats
    stats = lock_author_stats(raw_annotation)
    stats.serie_validations += 1
    stats.sample_validations += samples
    if raw_annotation.agrees_with:
        stats.serie_validations_concordant += 1
        stats.sample_validations_concordant += samples
        # Pay for all samples, but only if entire serie is concordant
        stats.earn_validations(samples)
    stats.save()

    # Update annotation author payment stats
    ref = raw_annotation.agrees_with
    if ref:
        if not ref.agreed:
            ref.agreed = True  # Prevent dup annotation stats and earnings
            ref_stats = lock_author_stats(ref)
            ref_stats.earn_annotations(samples)
            ref_stats.save()

        ref.agrees_with = raw_annotation
        ref.save()


@transaction.atomic
def update_canonical(canonical_pk):
    canonical = SeriesAnnotation.objects.select_for_update().get(pk=canonical_pk)
    raw_annos = canonical.raw_annotations.prefetch_related('sample_annotations') \
                                         .filter(is_active=True).order_by('pk')
    # Disable if no raw sources
    canonical.is_active = bool(raw_annos)

    best_cohens_kappa = max(a.best_kappa for a in raw_annos) if raw_annos else None

    # Update canonical sample annotations
    source = first(a for a in raw_annos if a.agrees_with_id) \
        or first(a for a in raw_annos if a.best_kappa == best_cohens_kappa and a.best_kappa > 0) \
        or first(raw_annos)
    if source and not is_samples_concordant(canonical, source):
        canonical.sample_annotations.all().delete()
        canonical.fill_samples([(s.sample_id, s.annotation)
                                for s in source.sample_annotations.all()])

    # Update canonical stats
    if source:
        canonical.column = source.column
        canonical.regex = source.regex
    # Calculate fleiss kappa for all existing annotations/validations
    canonical.fleiss_kappa = _fleiss_kappa([a.sample_annotations.all() for a in raw_annos]) \
        if raw_annos else None
    canonical.best_cohens_kappa = best_cohens_kappa
    canonical.annotations = raw_annos.count()
    canonical.authors = len(set(a.created_by_id for a in raw_annos))
    canonical.save()


def reschedule_validation(canonical):
    # Schedule revalidations with priority < 0, that's what new validations have,
    # to phase out garbage earlier
    if canonical.fleiss_kappa is None or math.isnan(canonical.fleiss_kappa):
        priority = -1
    else:
        priority = canonical.fleiss_kappa - 1

    # If failed too much then postpone next validation
    failed = canonical.raw_annotations.filter(is_active=True).count()
    if failed >= 5:
        priority = canonical.fleiss_kappa + 4

    ValidationJob.objects.create(annotation=canonical, priority=priority)


def _cohens_kappa(annos1, annos2):
    assert set(s.sample_id for s in annos1) == set(s.sample_id for s in annos2)

    categories = ldistinct(sv.annotation for sv in chain(annos1, annos2))
    category_index = {c: i for i, c in enumerate(categories)}

    table = np.zeros((len(categories), len(categories)))
    annos1 = sorted(annos1, key=attrgetter('sample_id'))
    annos2 = sorted(annos2, key=attrgetter('sample_id'))
    for sv1, sv2 in zip(annos1, annos2):
        table[category_index[sv1.annotation], category_index[sv2.annotation]] += 1

    return cohens_kappa(table, return_results=False)


def _fleiss_kappa(sample_sets):
    all_samples_annos = lcat(sample_sets)
    categories = ldistinct(sv.annotation for sv in all_samples_annos)
    category_index = {c: i for i, c in enumerate(categories)}

    stats = defaultdict(lambda: [0] * len(categories))
    for sv in all_samples_annos:
        stats[sv.sample_id][category_index[sv.annotation]] += 1

    return fleiss_kappa(stats.values())
