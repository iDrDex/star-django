import coreapi
import django_filters

from cacheops import cached_as
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from funcy import walk_keys

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

from tags.models import Tag, SeriesAnnotation, SampleAnnotation
from tags.annotate_core import save_annotation, save_validation, AnnotationError
from legacy.models import Platform, Series, Analysis, MetaAnalysis, PlatformProbe, Sample
from s3field.ops import frame_dumps
from analysis.analysis import get_analysis_df
from .serializers import (PlatformSerializer, SeriesSerializer, AnalysisSerializer,
                          AnalysisParamSerializer, SeriesAnnotationSerializer,
                          TagSerializer, MetaAnalysisSerializer,
                          SampleAnnotationValidator, SampleSerializer,
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
        case_query: `DF == 'DF' or hypertension == 'hypertension'`
        control_query: `PHT_Control == 'PHT_Control'
                            or hypertension_control == 'hypertension_control'`
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

    @list_route(url_path="probes/(?P<gpl_name>GPL\d+)")
    def probes(self, request, gpl_name):
        qs = PlatformProbe.objects.filter(platform__gpl_name=gpl_name)
        probes_df = qs.to_dataframe(
            fieldnames=['probe', 'mygene_sym', 'mygene_entrez']
        )
        return HttpResponse(frame_dumps(probes_df), content_type='application/json')


class SeriesAnnotationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SeriesAnnotation.objects.all()
    serializer_class = SeriesAnnotationSerializer

class SampleAnnotationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    KEYS = {
        'series_annotation__tag__tag_name': 'tag_name',
        'series_annotation__tag_id': 'tag_id',
        'series_annotation__tag__concept_full_id': 'tag_concept_full_id',
        'series_annotation__series__gse_name': 'gse_name',
        'series_annotation__series_id': 'serie_id',
        'series_annotation_id': 'series_annotation_id',
        'sample__gsm_name': 'gsm_name',
        'sample_id': 'sample_id',
        'sample__platform__gpl_name': 'gpl_name',
        'sample__platform_id': 'platform_id',
        'annotation': 'annotation',
    }

    @transaction.atomic
    def create(self, request):
        serializer = SampleAnnotationValidator(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        canonical = SeriesAnnotation.objects.filter(
            series=data['series'],
            tag=data['tag'],
            platform=data['platform']).first()

        data['user_id'] = request.user.id
        data['from_api'] = True
        data['tag_id'] = data['tag'].id
        data['series_id'] = data['series'].id
        del data['platform']
        del data['series']
        del data['tag']

        try:
            if canonical:
                save_validation(canonical.id, data)
            else:
                save_annotation(data)
        except AnnotationError as err:
            raise ValidationError(
                {'non_field_errors': [str(err)]})

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
                     'series_annotation__tag',
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


class SampleFilter(django_filters.rest_framework.FilterSet):
    series = django_filters.CharFilter(name='series__gse_name')
    platform = django_filters.CharFilter(name='platform__gpl_name')

    class Meta:
        model = Sample
        fields = ('series', 'platform')

class SampleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sample.objects.exclude(deleted='T').select_related('platform', 'series')
    serializer_class = SampleSerializer
    filter_class = SampleFilter

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
