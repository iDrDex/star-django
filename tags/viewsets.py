from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import SerieAnnotation, Tag
from .serializers import (PlatformSerializer,
                          SeriesSerializer,
                          AnalysisSerializer,
                          SerieAnnotationSerializer,
                          TagSerializer,
                          MetaAnalysisSerializer,
                          PlatformProbeSerializer,
                          )
from legacy.models import (Platform,
                           Series,
                           Analysis,
                           MetaAnalysis,
                           PlatformProbe,
                           )


class PlatformViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Series.objects.all()
    serializer_class = SeriesSerializer


class AnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Analysis.objects.filter(is_active=True)
    serializer_class = AnalysisSerializer
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, )
    search_fields = ('case_query', 'control_query', 'modifier_query', )
    filter_fields = ('specie', )


class SerieAnnotationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SerieAnnotation.objects.all()
    serializer_class = SerieAnnotationSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.filter(is_active=True)
    serializer_class = TagSerializer


class MetaAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetaAnalysis.objects.all()
    serializer_class = MetaAnalysisSerializer


class PlatformProbeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlatformProbe.objects.all()
    serializer_class = PlatformProbeSerializer
