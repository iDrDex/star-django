from funcy import group_by, project
from django.db import connection
from tags.models import (SeriesTag, SampleTag, ValidationJob,
                         SerieAnnotation, SerieValidation,
                         SampleValidation, )
from legacy.models import Sample
from tags.tasks import validation_workflow

class AnnotationError(Exception):
    pass

def save_annotation(data):
    user_id = data['user_id']
    annotations = data['annotations']

    sample_to_platform = dict(Sample.objects.filter(id__in=annotations)
                                    .values_list('id', 'platform_id'))
    groups = group_by(lambda (id, _): sample_to_platform[id], annotations.items())

    for platform_id, annotations in groups.items():
        series_tag = SeriesTag.objects.create(
            platform_id=platform_id,
            created_by_id=user_id,
            modified_by_id=user_id,
            header=data.get('column', ''),
            **project(data, ['series_id', 'tag_id', 'regex', 'note', 'from_api']))

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

    if not data.get('on_demand'):
        if series_tag.created_by_id == user_id:
            raise AnnotationError("You can't validate your own annotation")

        # Do not allow user validate same serie, same platform for same tag twice
        if SerieValidation.objects.filter(
                series_tag=series_tag, created_by_id=user_id).exists():
            raise AnnotationError('You had already validated this annotation')

    serie_validation = SerieValidation.objects.create(
        series_tag=series_tag, created_by_id=user_id,
        series_id=series_tag.series_id, platform_id=series_tag.platform_id,
        tag_id=series_tag.tag_id,
        **project(data, ['column', 'regexp', 'note', 'from_api', 'on_demand'])
    )

    # Create all sample validations
    SampleValidation.objects.bulk_create(
        SampleValidation(sample_id=sample_id, serie_validation=serie_validation,
                         annotation=annotation, created_by_id=user_id)
        for sample_id, annotation in annotations.iteritems())

    ValidationJob.objects.filter(series_tag=series_tag).delete()

    connection.on_commit(lambda: validation_workflow.delay(serie_validation.pk))

    return serie_validation
