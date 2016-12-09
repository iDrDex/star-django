from rest_framework import viewsets

from .models import SerieAnnotation, Tag, SeriesTag
from .serializers import (PlatformSerializer,
                          SeriesSerializer,
                          AnalysisSerializer,
                          SerieAnnotationSerializer,
                          TagSerializer,
                          SeriesTagSerializer, )
from legacy.models import Platform, Series, Analysis


class PlatformViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Series.objects.all()
    serializer_class = SeriesSerializer


class AnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer


class SerieAnnotationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SerieAnnotation.objects.all()
    serializer_class = SerieAnnotationSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class SeriesTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SeriesTag.objects.all()
    serializer_class = SeriesTagSerializer
