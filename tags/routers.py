from rest_framework import routers
from .viewsets import (PlatformViewSet,
                       SeriesViewSet,
                       AnalysisViewSet,
                       SerieAnnotationViewSet,
                       TagViewSet,
                       SeriesTagViewSet, )


router = routers.DefaultRouter()
router.register('platforms', PlatformViewSet)
router.register('series', SeriesViewSet)
router.register('analysis', AnalysisViewSet)
router.register('serie_annotations', SerieAnnotationViewSet)
router.register('tags', TagViewSet)
router.register('series_tag', SeriesTagViewSet)
