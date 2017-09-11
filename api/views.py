from django.http import HttpResponse
import djapi as api

from s3field.ops import frame_dumps
from legacy.models import Series, Sample, Platform, PlatformProbe, Analysis
from tags.models import Tag, SeriesAnnotation, SampleAnnotation
from tags.views import TagForm


PER_PAGE = 100


tags_qs = api.queryset(Tag).filter(is_active=True) \
    .values_but('created_by', 'modified_by', 'is_active', 'created_on', 'modified_on')

def tags(request):
    return api.json(tags_qs)

@api.auth_required
@api.user_passes_test(lambda user: user.is_competent)
@api.validate(TagForm)
def tag_create(request):
    raise NotImplementedError

def tag_detail(request, pk):
    return api.json(api.get_or_404(tags_qs, pk=pk))


series_qs = api.queryset(Series).values_but('id', 'samples_count').order_by('id')

def series(request):
    return api.json(api.paginate(request, series_qs, per_page=PER_PAGE))

def series_detail(request, gse_name):
    return api.json(api.get_or_404(series_qs, gse_name=gse_name))

@api.catch(Series.DoesNotExist, status=404)
def series_samples(request, gse_name):
    series = Series.objects.get(gse_name=gse_name)
    samples = api.queryset(series.samples.exclude(deleted='T')).values(
        'gsm_name', 'attrs',
        gse_name='series__gse_name', gpl_name='platform__gpl_name')

    # Filter by platform
    if request.GET.get('gpl_name'):
        samples = samples.filter(platform__gpl_name=request.GET.get('gpl_name'))

    return api.json(samples)


platforms_qs = api.queryset(Platform).order_by('id') \
    .values_but('id', 'stats', 'history', 'verdict', 'last_filled')

def platforms(request):
    return api.json(api.paginate(request, platforms_qs, per_page=PER_PAGE))

def platform_detail(request, gpl_name):
    return api.json(api.get_or_404(platforms_qs, gpl_name=gpl_name))

def platform_probes(request, gpl_name):
    if not Platform.objects.filter(gpl_name=gpl_name).exists():
        return api.json(404, detail='Platform not found')

    qs = PlatformProbe.objects.filter(platform__gpl_name=gpl_name)
    probes_df = qs.to_dataframe(
        fieldnames=['probe', 'mygene_sym', 'mygene_entrez']
    )
    return HttpResponse(frame_dumps(probes_df), content_type='application/json')


from s3field.fields import Resource
from analysis.views import AnalysisForm
from analysis.tasks import analysis_task

analysis_qs = api.queryset(Analysis).filter(is_active=True) \
    .values_but('created_by', 'modified_by', 'is_active', 'created_on', 'modified_on',
                'series_ids', 'platform_ids', 'sample_ids') \
    .map_types(Resource, lambda r: r.url)

def analysis_list(request):
    return api.json(api.paginate(request, analysis_qs, per_page=PER_PAGE))

def analysis_detail(request, pk):
    return api.json(api.get_or_404(analysis_qs, pk=pk))

def analysis_results(request, pk):
    analysis = Analysis.objects.filter(is_active=True, pk=pk).first()
    if not analysis:
        return api.json(404, detail='Analysis not found')
    if not analysis.success:
        return api.json(404, detail='Analysis failed or not finished yet')
    return HttpResponse(frame_dumps(analysis.results_df()), content_type='application/json')

@api.auth_required
@api.validate(AnalysisForm)
def analysis_create(request, analysis):
    analysis.created_by_id = analysis.modified_by_id = request.user.id
    analysis.save()
    analysis_task.delay(analysis.pk)
    return api.json(201, created=analysis.pk)


annotations_qs = api.queryset(SeriesAnnotation).filter(is_active=True) \
    .values_but('series_id', 'platform_id', 'series_tag', 'created_on', 'modified_on', 'is_active')\
    .values_add(gse_name='series__gse_name', gpl_name='platform__gpl_name')

def annotations(request):
    return api.json(api.paginate(request, annotations_qs, per_page=PER_PAGE))

def annotation_detail(request, pk):
    return api.json(api.get_or_404(annotations_qs, pk=pk))

def annotation_samples(request, pk):
    if not annotations_qs.filter(pk=pk).exists():
        return api.json(404, detail='Annotation not found')
    samples = api.queryset(SampleAnnotation).filter(series_annotation=pk) \
        .values_list('sample__gsm_name', 'annotation')
    return api.json(dict(samples))


from funcy import walk_keys
from django import forms
from django.core.exceptions import ValidationError
from tags.annotate_core import AnnotationError, save_annotation, save_validation

class AnnotateForm(forms.Form):
    tag = forms.ModelChoiceField(queryset=Tag.objects.filter(is_active=True),
                                 to_field_name='tag_name')
    series = forms.ModelChoiceField(queryset=Series.objects.all(), to_field_name='gse_name',
                                    widget=forms.TextInput)
    platform = forms.ModelChoiceField(queryset=Platform.objects.all(), to_field_name='gpl_name',
                                      widget=forms.TextInput)
    note = forms.CharField(required=False)
    annotations = api.JSONField()

    def clean_annotations(self):
        data = self.cleaned_data['annotations']
        if not isinstance(data, dict) or \
                not all(isinstance(k, basestring) and isinstance(v, basestring)
                        for k, v in data.items()):
            raise ValidationError("Annotations should be a dict of GSMs -> tag values")

        return data

    def clean(self):
        data = super(AnnotateForm, self).clean()

        # Check that platform and series match
        if data.get('series') and data.get('platform') \
                and data['platform'].gpl_name not in data['series'].platforms:
            raise ValidationError({'series': "Series %s doesn't contain platform %s"
                                   % (data['series'].gse_name, data['platform'].gpl_name)})

        # Remap sample annotations gsm -> id and check that they correspond to series/platform
        if data.get('annotations') and data.get('series') and data.get('platform'):
            samples_qs = Sample.objects.filter(series=data['series'], platform=data['platform'])
            gsm_to_id = dict(samples_qs.values_list('gsm_name', 'id'))
            all_samples = set(gsm_to_id)
            tagged_samples = set(data['annotations'])

            if all_samples - tagged_samples:
                self.add_error('annotations', "These samples are missing from annotations: %s"
                               % ', '.join(sorted(all_samples - tagged_samples)))
            if tagged_samples - all_samples:
                self.add_error('annotations', "These samples doesn't belong to series/platform: %s"
                               % ', '.join(sorted(tagged_samples - all_samples)))

            if data.get('annotations'):
                data['annotations'] = walk_keys(gsm_to_id, data['annotations'])

        return data

@api.auth_required
@api.user_passes_test(lambda user: user.is_competent)
@api.validate(AnnotateForm)
def annotate(request, data):
    canonical = SeriesAnnotation.objects.filter(
        series=data['series'],
        tag=data['tag'],
        platform=data['platform']).first()

    data['tag_id'] = data.pop('tag').id
    data['series_id'] = data.pop('series').id
    data['user_id'] = request.user.id
    data['from_api'] = True

    try:
        if canonical:
            save_validation(canonical.id, data)
        else:
            save_annotation(data)
    except AnnotationError as e:
        return api.json(409, detail=unicode(e))

    return HttpResponse(status=204)
