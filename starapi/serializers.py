from rest_framework import serializers

from legacy.models import (Platform,
                           Series,
                           Analysis,
                           MetaAnalysis,
                           PlatformProbe,
                           )
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
