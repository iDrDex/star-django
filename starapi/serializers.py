from funcy import all

from rest_framework import serializers

from legacy.models import Platform, Series, Analysis, MetaAnalysis, PlatformProbe
from tags.models import SerieAnnotation, Tag

from .fields import S3Field


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        exclude = ('stats', 'history',
                   'verdict', 'last_filled', )


class SeriesSerializer(serializers.ModelSerializer):
    attrs = serializers.JSONField()

    class Meta:
        model = Series
        fields = '__all__'


class AnalysisSerializer(serializers.ModelSerializer):
    df = S3Field()
    fold_changes = S3Field()

    class Meta:
        model = Analysis
        exclude = ['created_by', 'modified_by', 'is_active',
                   'created_on', 'modified_on', ]


class AnalysisParamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = ['specie', 'case_query',
                  'control_query', 'modifier_query', ]

    def __init__(self, *args, **kwargs):
        super(AnalysisParamSerializer, self).__init__(*args, **kwargs)
        self.fields['specie'].required = True
        self.fields['specie'].allow_blank = False


class SerieAnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerieAnnotation
        exclude = ['series_tag', 'created_on', 'modified_on', ]


class SampleAnnotationValidator(serializers.Serializer):
    tag = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    series = serializers.SlugRelatedField(queryset=Series.objects.all(), slug_field='gse_name')
    platform = serializers.SlugRelatedField(queryset=Platform.objects.all(), slug_field='gpl_name')
    note = serializers.CharField(required=False, default='')
    annotations = serializers.JSONField()

    def validate_annotations(self, annotations):
        if not all(isinstance(v, (unicode, str)) for v in annotations.values()):
            raise serializers.ValidationError(
                "Annotations should be a dict with serie tag id as a key and tag value as a value")

        if not all(isinstance(v, (unicode, str, int)) for v in annotations.keys()):
                raise serializers.ValidationError(
                    "Annotations should be a dict with serie tag id as a key and tag value as a value")

        return annotations

    def validate(self, data):
        samples = data['series'].samples.filter(
            platform=data['platform']).values('id', 'gsm_name')

        all_samples = {s['gsm_name'] for s in samples}
        gsm_to_id = {s['gsm_name']: s['id'] for s in samples}

        tagged_samples = set(data['annotations'])

        missing_annotations = all_samples - tagged_samples
        if missing_annotations:
            raise serializers.ValidationError(
                ["There are samples with ids {0} which are missing their annotation"
                 .format(missing_annotations)
                 ])

        extra_annotations = tagged_samples - all_samples
        if extra_annotations:
            raise serializers.ValidationError(
                "There is samples with id {0} which doesn't belongs to series {1}"
                .format(extra_annotations, data['series'].id))

        data['annotations'] = {gsm_to_id[key]: value
                               for key, value in data['annotations'].iteritems()}
        del data['platform']
        data['tag_id'] = data['tag'].id
        del data['tag']
        data['series_id'] = data['series'].id
        del data['series']

        return data

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        exclude = ['created_by', 'modified_by', 'is_active',
                   'created_on', 'modified_on', ]

class MetaAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaAnalysis
        fields = '__all__'

class PlatformProbeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformProbe
        fields = '__all__'
