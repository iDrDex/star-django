import coreapi

from cacheops import cached_as
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from funcy import walk_keys, first
from pandas.computation.ops import UndefinedVariableError
from rest_framework import viewsets, exceptions
from rest_framework.decorators import list_route
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.schemas import SchemaGenerator
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework_swagger import renderers

from tags.models import SerieAnnotation, Tag, SampleAnnotation, SeriesTag
from tags.misc import save_annotation, save_validation
from legacy.models import Platform, Series, Analysis, MetaAnalysis, PlatformProbe
from s3field.ops import frame_dumps
from analysis.analysis import get_analysis_df
from .serializers import (PlatformSerializer, SeriesSerializer, AnalysisSerializer,
                          AnalysisParamSerializer, SerieAnnotationSerializer,
                          TagSerializer, MetaAnalysisSerializer, PlatformProbeSerializer,
                          SampleAnnotationValidator,
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
    filter_fields = ('specie', 'case_query', 'control_query', 'modifier_query')

    @list_route()
    def df(self, request, format=None):
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
    df.action = 'list'

    @list_route(url_path="probes/(?P<gpl_name>[^/.]+)")
    def probes(self, request, gpl_name):
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
    permission_classes = [IsAuthenticatedOrReadOnly]
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

    @transaction.atomic
    def create(self, request):
        user_id = request.user.id

        serializer = SampleAnnotationValidator(
            data=request.data)
        serializer.is_valid(raise_exception=True)

        series = serializer.validated_data['series']
        tag = serializer.validated_data['tag']

        series_tag = first(SeriesTag.objects.filter(series=series, tag=tag))

        if not series_tag:
            # create annotation
            save_annotation(user_id, serializer.validated_data, True)
        else:
            # create validation
            if series_tag.created_by.id == user_id:
                raise ValidationError(
                    {'non_field_errors': "You can't validate your own annotation"})

            res, err = save_validation(user_id, series_tag, serializer.validated_data, True)
            if not res:
                raise ValidationError(
                    {'non_field_errors': err})

        return Response(status=201)

    def list(self, request, format=None):
        """
        Download all samples annotations.  
        This API method return the huge amout of data.  
        Please use [this link](/api/sample_annotations.json) to dowload all samples annotations.
        """
        @cached_as(SampleAnnotation)
        def get_annotation():
            return JsonResponse(
                [walk_keys(self.KEYS, annotation) for annotation in
                 SampleAnnotation.objects.values(*self.KEYS).prefetch_related(
                     'sample',
                     'sample__platform',
                     'serie_annotation__tag',
                ).iterator()],
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


class SwaggerSchemaView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True
    permission_classes = [AllowAny]
    renderer_classes = [
        CoreJSONRenderer,
        renderers.OpenAPIRenderer,
        renderers.SwaggerUIRenderer
    ]

    def get(self, request):
        generator = SchemaGenerator(
            title="Stargeo API",
        )
        schema = generator.get_schema(request=request)
        schema['analysis']['df']._fields = [
            coreapi.Field(name='specie', required=True),
            coreapi.Field(name='case_query', required=True),
            coreapi.Field(name='control_query', required=True),
            coreapi.Field(name='modifier_query', required=False),
        ]

        if not schema:
            raise exceptions.ValidationError(
                'The schema generator did not return a schema Document'
            )

        return Response(schema)
