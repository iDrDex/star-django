from rest_framework import serializers

from .models import SerieAnnotation, Tag
from legacy.models import (Platform,
                           Series,
                           Analysis,
                           MetaAnalysis,
                           PlatformProbe,
                           )
from s3field.ops import generate_url


class S3Field(serializers.Field):
    def to_representation(self, obj):
        return generate_url(obj)


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
