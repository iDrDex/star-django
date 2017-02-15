from funcy import walk_keys, all, first

from rest_framework import serializers

from legacy.models import Platform, Series, Analysis, MetaAnalysis, PlatformProbe
from tags.models import SerieAnnotation, Tag, SeriesTag
from tags.misc import save_annotation

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


class CreateSampleAnnotationSerializer(serializers.Serializer):
    series = serializers.PrimaryKeyRelatedField(queryset=Series.objects.all())
    tag = serializers.PrimaryKeyRelatedField(queryset=SeriesTag.objects.all())
    column = serializers.CharField(max_length=512, required=False)
    values = serializers.JSONField()

    def validate_values(self, value):
        try:
            value = walk_keys(int, value)
        except Exception as err:
            raise serializers.ValidationError(str(err))

        if not all(isinstance(v, (unicode, str)) for v in value.values()):
            raise serializers.ValidationError(
                "Values should be a dict with serie tag id as a key and tag value as a value")

        return value

    def create(self, validated_data):
        series = validated_data['series']
        tag = validated_data['tag']
        column = validated_data.get('column', '')
        values = validated_data['values']

        old_annotation = first(SeriesTag.objects.filter(series=series, tag=tag))

        if not old_annotation:
            # create annotation
            save_annotation(self.context.user.id, series.id, tag.id, values, column)
        else:
            # create validation
            pass
        return []


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
