from cacheops import FileCache
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from funcy import partial, walk_keys
from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from tags.models import SerieAnnotation, Tag, SampleAnnotation
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
file_cache = FileCache('/tmp/cacheops_sample_annotations')


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
        Download analysis data frame  
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

class SampleAnnotationViewSet(viewsets.ViewSet):
    KEYS = {
        'serie_annotation__tag__tag_name': 'tag_name',
        'serie_annotation__tag_id': 'tag_id',
        'serie_annotation__tag__concept_full_id': 'tag_concept_full_id',
        'serie_annotation__series__gse_name': 'gse_name',
        'serie_annotation__series_id': 'serie_id',
        'serie_annotation_id': 'serie_annotation_id',
        'sample__gsm_name': 'gsm_name',
        'sample_id': 'sample_id',
        'sample__platform__gpl_name': 'gpl_name',
        'sample__platform_id': 'platform_id',
        'annotation': 'annotation',
    }

    def list(self, request, format=None):
        """
        Download all samples annotations.  
        This API method return the huge amout of data.  
        Please use [this link](/api/sample_annotations.json) to dowload all samples annotations.
        """
        @file_cache.cached_view(timeout=60 * 60)
        def handle(request):
            data = map(
                partial(walk_keys, self.KEYS),
                SampleAnnotation.objects.values(*self.KEYS).prefetch_related(
                    'sample',
                    'sample__platform',
                    'serie_annotation__tag',
                ).iterator())

            return JsonResponse(data, safe=False, content_type='application/octet-stream')
        return handle(request._request)



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
