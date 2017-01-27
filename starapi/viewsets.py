from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
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
from pandas.computation.ops import UndefinedVariableError
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
        """
        **Example of valid request data**
        ```
        {
            "specie": "human",
            "case_query": "PHT == 'PHT' or hypertension == 'hypertension'",
            "control_query": "PHT_Control == 'PHT_Control' or hypertension_control == 'hypertension_control'"
        }
        ```
        You can copy it and paste to input below to perform a API request.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis = Analysis(**serializer.data)
        try:
            return Response(get_analysis_df(analysis))
        except UndefinedVariableError as err:
            data = {'error': str(err)}
            return Response(status=400, data=data)


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

    @detail_route(methods=['get'], lookup_url_kwarg="gpl_name")
    def get_probes(self, request, gpl_name):
        qs = PlatformProbe.objects.filter(
            platform__gpl_name=gpl_name).order_by('id')
        probes_df = qs.to_dataframe(
            fieldnames=['probe', 'mygene_sym', 'mygene_entrez']
        )
        return Response(probes_df)
