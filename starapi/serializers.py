from funcy import walk_keys, all, first, compact

from rest_framework import serializers

from legacy.models import Platform, Series, Analysis, MetaAnalysis, PlatformProbe
from tags.models import SerieAnnotation, Tag, SeriesTag
from tags.misc import save_annotation, save_validation, SaveValidatonError

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
    tag = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    column = serializers.CharField(max_length=512, required=False)
    values = serializers.JSONField()
    # values field is a json object with sample_id as keys and tag value as values

    def validate_values(self, value):
        try:
            value = walk_keys(int, value)
        except Exception as err:
            raise serializers.ValidationError(str(err))

        if not all(isinstance(v, (unicode, str)) for v in value.values()):
            raise serializers.ValidationError(
                "Values should be a dict with serie tag id as a key and tag value as a value")

        return value

    def validate(self, data):
        tagged_samples_ids = set(data['values'].keys())
        all_samples_ids = set(data['series'].samples.values_list('id', flat=True))
        missing_annotations = all_samples_ids - tagged_samples_ids
        extra_annotations = tagged_samples_ids - all_samples_ids

        if missing_annotations == extra_annotations == set():
            return data

        missing_text = "There are samples with id {0} which are missing their annotation"\
                       .format(list(missing_annotations)) \
                       if missing_annotations else None
        extra_text = "There are samples with id {0} which doesn't belongs to series {1}"\
                     .format(list(extra_annotations), data['series'].id) \
                     if extra_annotations else None

        raise serializers.ValidationError(compact([missing_text, extra_text]))

    def create(self, validated_data):
        user_id = self.context['user'].id
        series = validated_data['series']
        tag = validated_data['tag']
        column = validated_data.get('column', '')
        values = validated_data['values']

        series_tag = first(SeriesTag.objects.filter(series=series, tag=tag))

        if not series_tag:
            # create annotation
            return save_annotation(user_id, series.id, tag.id, values, column)
        else:
            # create validation
            if series_tag.created_by.id == user_id:
                raise serializers.ValidationError(
                    {'non_field_errors': "You can't validate your own annotation"})
            try:
                return save_validation(user_id, series_tag, values, column)
            except SaveValidatonError as err:
                raise serializers.ValidationError(
                    {'non_field_errors': unicode(err)})


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
