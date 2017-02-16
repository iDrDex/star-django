from funcy import group_by

from legacy.models import Sample
from tags.models import (SeriesTag, SampleTag, ValidationJob,
                         SerieAnnotation, SerieValidation,
                         SampleValidation, )


def save_annotation(user_id, data, from_api=False):
    # Group samples by platform
    sample_to_platform = dict(Sample.objects.filter(id__in=data['values'])
                                    .values_list('id', 'platform_id'))
    groups = group_by(lambda (id, _): sample_to_platform[id], data['values'].items())
    # Save all annotations and used regexes
    for platform_id, annotations in groups.items():
        # Do not allow for same user to annotate same serie twice
        series_tag, _ = SeriesTag.objects.get_or_create(
            series=data['series'], platform_id=platform_id, tag=data['tag'], created_by_id=user_id,
            defaults=dict(header=data['column'], regex=data['regex'],
                          modified_by_id=user_id, from_api=from_api,
                          comment=data['comment'])
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


def save_validation(user_id, series_tag, data, from_api=False):
    serie_validation, created = SerieValidation.objects.get_or_create(
        series_tag_id=series_tag.id, created_by_id=user_id,
        defaults=dict(
            column=data['column'], regex=data['regex'],
            series_id=series_tag.series_id,
            platform_id=series_tag.platform_id, tag_id=series_tag.tag_id,
            from_api=from_api, comment=data['comment'],
        )
    )
    # Do not allow user validate same serie, same platform for same tag twice
    if not created:
        return False, 'You had already validated this annotation'

    # Create all sample validations
    SampleValidation.objects.bulk_create([
        SampleValidation(sample_id=sample_id, serie_validation=serie_validation,
                         annotation=annotation, created_by_id=user_id)
        for sample_id, annotation in data['values'].items()
    ])

    return serie_validation, ''
