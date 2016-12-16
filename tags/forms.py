import json

from dal import autocomplete
from django import forms
from django.core.urlresolvers import reverse
from django.db import transaction
from funcy import group_by, first

from .models import Tag, SeriesTag, SampleTag, ValidationJob, SerieAnnotation
from legacy.models import Sample


class AnnotationForm(forms.Form):
    tag_id = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='available_series_tag_autocomplete')
    )
    column = forms.CharField(required=False)
    regex = forms.CharField()
    values = forms.CharField()

    def __init__(self, series_id, *args, **kwargs):
        self.series_id = series_id
        super(AnnotationForm, self).__init__(*args, **kwargs)
        self.fields['tag_id'].widget.url = reverse(
            self.fields['tag_id'].widget._url,
            args=[series_id])

    def save(self, user_id):
        series_id = self.series_id
        tag_id = self.data['tag_id']
        column = self.data['column']
        regex = self.data['regex']
        values = dict(json.loads(self.data['values']))

        with transaction.atomic():
            # Group samples by platform
            sample_to_platform = dict(Sample.objects.filter(id__in=values)
                                      .values_list('id', 'platform_id'))
            groups = group_by(lambda (id, _): sample_to_platform[id],
                              values.items())

            old_annotation = first(SeriesTag.objects.filter(
                series_id=series_id,
                tag_id=tag_id))
            if old_annotation:
                return False, 'Serie %s is already annotated with tag %s' %\
                    (old_annotation.series.gse_name,
                      old_annotation.tag.tag_name)

            # Save all annotations and used regexes
            for platform_id, annotations in groups.items():
                # Do not allow for same user to annotate same serie twice
                series_tag, _ = SeriesTag.objects.get_or_create(
                    series_id=series_id,
                    platform_id=platform_id,
                    tag_id=tag_id,
                    created_by_id=user_id,
                    defaults=dict(header=column,
                                  regex=regex,
                                  modified_by_id=user_id)
                )

                # TODO: check if this can result in sample tags doubling
                # Create all sample tags
                sample_tags = SampleTag.objects.bulk_create([
                    SampleTag(sample_id=sample_id,
                              series_tag=series_tag,
                              annotation=annotation,
                              created_by_id=user_id,
                              modified_by_id=user_id)
                    for sample_id, annotation in annotations
                ])

                # Create validation job
                ValidationJob.objects.create(series_tag=series_tag)

                # Create canonical annotation
                sa = SerieAnnotation.create_from_series_tag(series_tag)
                sa.fill_samples(sample_tags)
        return True, 'Saved annotations'
