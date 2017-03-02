from tags.models import (SeriesTag, SampleTag, ValidationJob,
                         SerieAnnotation, SerieValidation,
                         SampleValidation, )


def save_annotation(data, from_api=False):
    series = data['series']
    tag = data['tag']
    platform = data['platform']

    series_tag = SeriesTag.objects.filter(
        series=series, tag=tag,
        platform=platform, is_active=True).first()

    if series_tag:
        return save_validation(series_tag, data, from_api)

    user_id = data['user_id']
    series = data['series']
    platform = data['platform']
    tag = data['tag']
    annotations = data['annotations'].iteritems()

    series_tag, _ = SeriesTag.objects.get_or_create(
        series=series, platform=platform,
        tag=tag, created_by_id=user_id,
        defaults=dict(header=data.get('column', ''), regex=data.get('regex', ''),
                      modified_by_id=user_id, from_api=from_api,
                      note=data.get('note', ''))
    )

    sample_tags = SampleTag.objects.bulk_create([
        SampleTag(sample_id=sample_id, series_tag=series_tag, annotation=annotation,
                  created_by_id=user_id, modified_by_id=user_id)
        for sample_id, annotation in annotations
    ])

    ValidationJob.objects.create(series_tag=series_tag)

    sa = SerieAnnotation.create_from_series_tag(series_tag)
    sa.fill_samples(sample_tags)

    return sa, ''


def save_validation(series_tag, data, from_api=False):
    user_id = data['user_id']
    annotations = data['annotations'].iteritems()

    if series_tag.created_by.id == user_id:
        return None, "You can't validate your own annotation"

    serie_validation, created = SerieValidation.objects.get_or_create(
        series_tag=series_tag, created_by_id=user_id,
        defaults=dict(
            column=data.get('column', ''), regex=data.get('regex', ''),
            series_id=series_tag.series_id,
            platform_id=series_tag.platform_id, tag_id=series_tag.tag_id,
            from_api=from_api, note=data.get('note', ''),
        )
    )
    # Do not allow user validate same serie, same platform for same tag twice
    if not created:
        return None, 'You had already validated this annotation'

    # Create all sample validations
    SampleValidation.objects.bulk_create(
        SampleValidation(sample_id=sample_id, serie_validation=serie_validation,
                         annotation=annotation, created_by_id=user_id)
        for sample_id, annotation in annotations)

    ValidationJob.objects.get(series_tag=series_tag).delete()

    return serie_validation, ''
