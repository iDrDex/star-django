from rest_framework import serializers

from .models import SerieAnnotation, Tag, SeriesTag
from legacy.models import Platform, Series, Analysis
from s3field.ops import generate_url


class PlatformSerializer(serializers.ModelSerializer):
    stats = serializers.JSONField()
    history = serializers.JSONField()

    class Meta:
        model = Platform
        fields = '__all__'


class SeriesSerializer(serializers.ModelSerializer):
    attrs = serializers.JSONField()

    class Meta:
        model = Series
        fields = '__all__'


class S3Field(serializers.Field):
    def to_representation(self, obj):
        return generate_url(obj)


class AnalysisSerializer(serializers.ModelSerializer):
    df = S3Field()
    fold_changes = S3Field()

    class Meta:
        model = Analysis
        exclude = ['created_by', 'modified_by']


class SerieAnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SerieAnnotation
        fields = '__all__'


class SeriesTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesTag
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
