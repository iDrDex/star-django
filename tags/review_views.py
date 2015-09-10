from funcy import group_by
from datatableview.views import DatatableView
from datatableview.utils import DatatableOptions

from tags.models import SerieAnnotation


# NOTE: to filter in a special way on GSE\d+ and GPL\d+ we parse options diffrently,
#       and later filter queryset by that.

class AnnotationsSearchOptions(DatatableOptions):
    def _normalize_options(self, query, options):
        options = DatatableOptions._normalize_options(self, query, options)

        filters = group_by(r'^(GSE|GPL|)', options['search'].split())
        options['search'] = ''.join(filters.pop('', []))
        options['filters'] = filters

        return options


class SeriesAnnotations(DatatableView):
    model = SerieAnnotation
    template_name = 'tags/reviews/series.j2'
    datatable_options = {
        'columns': [
            'id',
            ('Series', 'series__gse_name'),
            ('Platform', 'platform__gpl_name'),
            ('Tag', 'tag__tag_name'),
            'annotations',
            'authors',
            'fleiss_kappa',
            'best_cohens_kappa',
        ]
    }
    datatable_options_class = AnnotationsSearchOptions

    def get_queryset(self):
        return SerieAnnotation.objects.select_related('series', 'platform', 'tag')

    def apply_queryset_options(self, queryset):
        options = self._get_datatable_options()

        if options['filters']['GSE']:
            queryset = queryset.filter(series__gse_name__in=options['filters']['GSE'])
        if options['filters']['GPL']:
            queryset = queryset.filter(platform__gpl_name__in=options['filters']['GPL'])

        return super(SeriesAnnotations, self).apply_queryset_options(queryset)


series_annotations = SeriesAnnotations.as_view()
