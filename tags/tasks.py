from celery import shared_task
from django.db import transaction

from .models import SerieValidation


@shared_task(acks_late=True)
@transaction.atomic('legacy')
def calc_validation_stats(serie_validation_pk):
    serie_validation = SerieValidation.objects.get(pk=serie_validation_pk)

    sample_validations = serie_validation.sample_validations.all()
    tags_by_sample = {obj.sample_id: obj for obj in serie_validation.series_tag.sample_tags.all()}

    for sv in sample_validations:
        sample_tag = tags_by_sample[sv.sample_id]
        sv.concordant = sv.annotation == (sample_tag.annotation or '')
        sv.save()

    serie_validation.samples_total = len(sample_validations)
    serie_validation.samples_concordant = sum(s.concordant for s in sample_validations)
    serie_validation.samples_concordancy \
        = float(serie_validation.samples_concordant) / serie_validation.samples_total
    serie_validation.save()
