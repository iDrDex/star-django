from rest_framework import viewsets, filters
from rest_framework.decorators import list_route
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from tags.models import SerieAnnotation, Tag
from legacy.models import (Platform,
                           Series,
                           Analysis,
                           MetaAnalysis,
                           PlatformProbe,
                           )
from analysis.analysis import get_analysis_df
from .serializers import (PlatformSerializer,
                          SeriesSerializer,
                          AnalysisSerializer,
                          AnalysisParamSerializer,
                          SerieAnnotationSerializer,
                          TagSerializer,
                          MetaAnalysisSerializer,
                          PlatformProbeSerializer,
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

    @list_route(methods=['post'], serializer_class=AnalysisParamSerializer)
    def get_analysis_df(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis = Analysis(**serializer.data)
        return Response(get_analysis_df(analysis))


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
