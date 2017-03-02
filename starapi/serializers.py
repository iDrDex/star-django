from funcy import all, compact, map, first

from rest_framework import serializers

from legacy.models import Platform, Series, Analysis, MetaAnalysis, PlatformProbe, Sample
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


def ids_to_gsms(ids):
    return Sample.objects.filter(id__in=ids).values_list('gsm_name', flat=True)


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
        samples = data['series'].samples.values_list('id', 'gsm_name')

        gsm_to_id = {s[1].upper(): s[0] for s in samples}

        try:
            annotations = {
                gsm_to_id[key.upper()]: value
                for key, value in data['annotations'].iteritems()
            }
        except KeyError as err:
            raise serializers.ValidationError(
                "There is samples with id {0} which doesn't belongs to series {1}"
                .format(err.message, data['series'].id))
        except ValueError as err:
            raise serializers.ValidationError(unicode(err))

        tagged_samples_ids = set(annotations.keys())
        all_samples_ids = set(map(first, samples))
        missing_annotations = all_samples_ids - tagged_samples_ids

        if missing_annotations == set():
            data['annotations'] = annotations
            return data

        raise serializers.ValidationError(
            ["There are samples with ids {0} which are missing their annotation"
             .format(ids_to_gsms(missing_annotations))
             ])

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
