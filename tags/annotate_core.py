from funcy import group_by, project
from tags.models import (SeriesTag, SampleTag, ValidationJob,
                         SerieAnnotation, SerieValidation,
                         SampleValidation, )
from legacy.models import Sample
from tags.tasks import validation_workflow

class AnnotationError(Exception):
    pass

def save_annotation(data):
    user_id = data['user_id']
    series_id = data['series_id']
    tag_id = data['tag_id']
    annotations = data['annotations']

    sample_to_platform = dict(Sample.objects.filter(id__in=annotations)
                              .values_list('id', 'platform_id'))
    groups = group_by(lambda (id, _): sample_to_platform[id], annotations.items())

    for platform_id, annotations in groups.items():
        series_tag = SeriesTag.objects.filter(
            series_id=series_id, tag_id=tag_id,
            platform_id=platform_id, is_active=True).first()

        if series_tag:
            save_validation(series_tag.id, data)

        series_tag, _ = SeriesTag.objects.get_or_create(
            series_id=series_id, tag_id=tag_id,
            platform_id=platform_id, created_by_id=user_id,
            defaults=dict(
                modified_by_id=user_id,
                header=data.get('column', ''),
                **project(data, ['regex', 'note', 'from_api'])))

        sample_tags = SampleTag.objects.bulk_create([
            SampleTag(sample_id=sample_id, series_tag=series_tag, annotation=annotation,
                      created_by_id=user_id, modified_by_id=user_id)
            for sample_id, annotation in annotations
        ])

        ValidationJob.objects.create(series_tag=series_tag)

        sa = SerieAnnotation.create_from_series_tag(series_tag)
        sa.fill_samples(sample_tags)


def save_validation(series_tag_id, data):
    annotations = data['annotations']
    series_tag = SeriesTag.objects.get(id=series_tag_id)
    user_id = data['user_id']

    import ipdb; ipdb.set_trace()
    if not data.get('on_demand') and series_tag.created_by_id == user_id:
        raise AnnotationError("You can't validate your own annotation")

    serie_validation, created = SerieValidation.objects.get_or_create(
        series_tag=series_tag, created_by_id=user_id,
        defaults=dict(
            series_id=series_tag.series_id, platform_id=series_tag.platform_id,
            tag_id=series_tag.tag_id,
            **project(data, ['column', 'regexp', 'note', 'from_api', 'on_demand'])
        )
    )
    # Do not allow user validate same serie, same platform for same tag twice
    if not created:
        raise AnnotationError('You had already validated this annotation')

    # Create all sample validations
    SampleValidation.objects.bulk_create(
        SampleValidation(sample_id=sample_id, serie_validation=serie_validation,
                         annotation=annotation, created_by_id=user_id)
        for sample_id, annotation in annotations.iteritems())

    validation_workflow.delay(serie_validation.pk)

    ValidationJob.objects.filter(series_tag=series_tag).delete()

    return serie_validation
