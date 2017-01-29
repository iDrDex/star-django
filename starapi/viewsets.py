from cacheops import cached_as
from django.http import JsonResponse, HttpResponse
from funcy import partial, walk_keys
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from tags.models import SerieAnnotation, Tag, SampleAnnotation
from legacy.models import (Platform,
                           Series,
                           Analysis,
                           MetaAnalysis,
                           PlatformProbe,
                           )
from s3field.ops import frame_dumps
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
    pagination_class = None
    serializer_class = AnalysisSerializer
    filter_fields = ('specie', 'case_query', 'control_query', 'modifier_query')

    def list(self, request, format=None):
        """
        Download analysis data frame  
        **Example of valid filter data**  
        specie: `human`  
        case_query: `PHT == 'PHT' or hypertension == 'hypertension'`  
        control_query: `PHT_Control == 'PHT_Control' or hypertension_control == 'hypertension_control'`  
        You can copy it and paste to inputs below to perform a API request.
        """
        serializer = AnalysisParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        analysis = Analysis(**serializer.data)
        try:
            df = get_analysis_df(analysis)
            return HttpResponse(frame_dumps(df), content_type='application/json')
        except UndefinedVariableError as err:
            data = {'error': str(err)}
            return Response(status=400, data=data)

    @list_route(methods=['get'], url_path="probes/(?P<gpl_name>[^/.]+)")
    def get_probes(self, request, gpl_name):
        qs = PlatformProbe.objects.filter(
            platform__gpl_name=gpl_name).order_by('id')
        probes_df = qs.to_dataframe(
            fieldnames=['probe', 'mygene_sym', 'mygene_entrez']
        )
        return HttpResponse(frame_dumps(probes_df), content_type='application/json')


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
        @cached_as(SampleAnnotation)
        def get_annotation():
            return JsonResponse(
                map(
                    partial(walk_keys, self.KEYS),
                    SampleAnnotation.objects.values(*self.KEYS).prefetch_related(
                        'sample',
                        'sample__platform',
                        'serie_annotation__tag',
                    ).iterator()),
                safe=False)
        response = get_annotation()
        response['Content-Type'] = 'application/octet-stream' if format == 'json'\
                                   else 'application/json'
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.filter(is_active=True)
    serializer_class = TagSerializer


class MetaAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetaAnalysis.objects.all()
    serializer_class = MetaAnalysisSerializer


class PlatformProbeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PlatformProbe.objects.all()
    serializer_class = PlatformProbeSerializer
