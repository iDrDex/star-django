from funcy import group_by

from django.db import transaction

from legacy.models import Sample
from tags.models import (SeriesTag, SampleTag, ValidationJob,
                         SerieAnnotation, SerieValidation,
                         SampleValidation, )


@transaction.atomic
def save_annotation(
        user_id,
        series_id,
        tag_id,
        values,
        column='',
        regex=''):
    # Group samples by platform
    sample_to_platform = dict(Sample.objects.filter(id__in=values)
                                    .values_list('id', 'platform_id'))
    groups = group_by(lambda (id, _): sample_to_platform[id], values.items())
    # Save all annotations and used regexes
    for platform_id, annotations in groups.items():
        # Do not allow for same user to annotate same serie twice
        series_tag, _ = SeriesTag.objects.get_or_create(
            series_id=series_id, platform_id=platform_id, tag_id=tag_id, created_by_id=user_id,
            defaults=dict(header=column, regex=regex, modified_by_id=user_id)
        )

        # TODO: check if this can result in sample tags doubling
        # Creat e all sample tags
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

    return []


class SaveValidatonError(Exception):
    pass

@transaction.atomic
def save_validation(
        user_id,
        series_tag,
        values,
        column='',
        regex=''):
    serie_validation, created = SerieValidation.objects.get_or_create(
        series_tag_id=series_tag.id, created_by_id=user_id,
        defaults=dict(
            column=column, regex=regex,
            series_id=series_tag.series_id,
            platform_id=series_tag.platform_id, tag_id=series_tag.tag_id
        )
    )
    # Do not allow user validate same serie, same platform for same tag twice
    if not created:
        raise SaveValidatonError('You had already validated this annotation')

    # Create all sample validations
    SampleValidation.objects.bulk_create([
        SampleValidation(sample_id=sample_id, serie_validation=serie_validation,
                         annotation=annotation, created_by_id=user_id)
        for sample_id, annotation in values.items()
    ])

    return serie_validation
