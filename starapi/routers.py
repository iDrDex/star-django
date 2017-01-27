from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

from .viewsets import (PlatformViewSet,
                       SeriesViewSet,
                       AnalysisViewSet,
                       SerieAnnotationViewSet,
                       SampleAnnotationViewSet,
                       TagViewSet,
                       MetaAnalysisViewSet,
                       PlatformProbeViewSet
                       )

class StarApiRouter(DefaultRouter):
    def get_lookup_regex(self, viewset, view):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.
        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.
        https://github.com/alanjds/drf-nested-routers
        """
        base_regex = '(?P<{lookup_url_kwarg}>{lookup_value})'
        # Use `pk` as default field, unset set.  Default regex should not
        # consume `.json` style suffixes and should break at '/' boundaries.
        lookup_field = view.initkwargs.get(
            'lookup_field',
            getattr(viewset, 'lookup_field', 'pk')
        )
        lookup_url_kwarg = view.initkwargs.get(
            'lookup_url_kwarg',
            getattr(viewset, 'lookup_url_kwarg', None) or lookup_field
        )
        lookup_value = view.initkwargs.get(
            'lookup_value_regex',
            getattr(viewset, 'lookup_value_regex', '[^/.]+')
        )
        return base_regex.format(
            lookup_url_kwarg=lookup_url_kwarg,
            lookup_value=lookup_value
        )

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = []

        for prefix, viewset, basename in self.registry:
            routes = self.get_routes(viewset)

            for route in routes:

                # Only actions which actually exist on the viewset will be bound
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                view = viewset.as_view(mapping, **route.initkwargs)
                # Build the url pattern
                regex = route.url.format(
                    prefix=prefix,
                    lookup=self.get_lookup_regex(viewset, view),
                    trailing_slash=self.trailing_slash
                )

                # If there is no prefix, the first part of the url is probably
                #   controlled by project's urls.py and the router is in an app,
                #   so a slash in the beginning will (A) cause Django to give
                #   warnings and (B) generate URLS that will require using '//'.
                if not prefix and regex[:2] == '^/':
                    regex = '^' + regex[2:]

                name = route.name.format(basename=basename)
                urls.append(url(regex, view, name=name))

        if self.include_root_view:
            if self.schema_title:
                view = self.get_schema_root_view(api_urls=urls)
            else:
                view = self.get_api_root_view(api_urls=urls)
            root_url = url(r'^$', view, name=self.root_view_name)
            urls.append(root_url)

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)

        return urls


router = StarApiRouter()
router.register('platforms', PlatformViewSet)
router.register('series', SeriesViewSet)
router.register('analysis', AnalysisViewSet)
router.register('serie_annotations', SerieAnnotationViewSet)
router.register('sample_annotations', SampleAnnotationViewSet, base_name='sampleannotation')
router.register('tags', TagViewSet)
router.register('meta_analysis', MetaAnalysisViewSet)
router.register('platform_probe', PlatformProbeViewSet)
