from rest_framework.routers import DefaultRouter

from .viewsets import (PlatformViewSet,
                       SeriesViewSet,
                       AnalysisViewSet,
                       SerieAnnotationViewSet,
                       SampleAnnotationViewSet,
                       TagViewSet,
                       MetaAnalysisViewSet,
                       SampleViewSet,
                       )

router = DefaultRouter()
router.register('platforms', PlatformViewSet)
router.register('series', SeriesViewSet)
router.register('analysis', AnalysisViewSet)
router.register('serie_annotations', SerieAnnotationViewSet)
router.register('sample_annotations', SampleAnnotationViewSet, base_name='sampleannotation')
router.register('tags', TagViewSet)
router.register('meta_analysis', MetaAnalysisViewSet)
router.register('samples', SampleViewSet)
