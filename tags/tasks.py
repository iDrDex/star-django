import logging
from celery import shared_task
from django.db import transaction

from .models import SerieValidation, UserStats


logger = logging.getLogger(__name__)


@shared_task(acks_late=True)
@transaction.atomic('legacy')
def calc_validation_stats(serie_validation_pk):
    serie_validation = SerieValidation.objects.select_for_update().get(pk=serie_validation_pk)
    # Guard from double update, so that user stats won't be messed up
    if serie_validation.samples_total is not None:
        return

    sample_validations = serie_validation.sample_validations.all()
    tags_by_sample = {obj.sample_id: obj for obj in serie_validation.series_tag.sample_tags.all()}

    # Check if samples set is the same
    if set(tags_by_sample) != set(sv.sample_id for sv in sample_validations):
        logger.error('Samples sets differ for serie validation %s and its annotation',
                     serie_validation_pk)
        return

    for sv in sample_validations:
        sample_tag = tags_by_sample[sv.sample_id]
        sv.concordant = sv.annotation == (sample_tag.annotation or '')
        sv.save()

    serie_validation.samples_total = len(sample_validations)
    serie_validation.samples_concordant = sum(s.concordant for s in sample_validations)
    if sample_validations:
        serie_validation.samples_concordancy \
            = float(serie_validation.samples_concordant) / serie_validation.samples_total
    serie_validation.save()

    # Update validating user stats
    stats, _ = UserStats.objects.select_for_update() \
        .get_or_create(user_id=serie_validation.created_by_id)
    stats.serie_validations += 1
    stats.sample_validations += serie_validation.samples_total
    if serie_validation.concordant:
        stats.serie_validations_concordant += 1
    stats.sample_validations_concordant += serie_validation.samples_concordant

    # Pay for all samples, but only if entire serie is concordant
    if serie_validation.concordant:
        stats.samples_to_pay_for += serie_validation.samples_total
    stats.save()

    # Update annotation author payment stats
    if serie_validation.concordant:
        author_id = serie_validation.series_tag.created_by_id
        author_stats, _ = UserStats.objects.select_for_update().get_or_create(user_id=author_id)
        author_stats.samples_to_pay_for += serie_validation.samples_total
        author_stats.save()
