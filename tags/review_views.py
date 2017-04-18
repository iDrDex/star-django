from funcy import group_by, cached_property, partial, walk_keys, map
from datatableview.views import DatatableView
from datatableview.utils import DatatableOptions

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from tags.models import SeriesTag, SerieAnnotation, SerieValidation, \
    SampleAnnotation, SampleValidation
from .tasks import validation_workflow


class AnnotationsSearchOptions(DatatableOptions):
    def _normalize_options(self, query, options):
        """
        Here we parse some search tokens diffrently to enable filtering:
            GSE\d+ and GPL\d+    filter by specific serie or platform
            tag=\w+              filters by tag
            valid                selects validated annotations
        """
        options = DatatableOptions._normalize_options(self, query, options)

        filters = group_by(r'^(GSE|GPL|[Tt]ag=|valid)', options['search'].split())
        options['search'] = ' '.join(filters.pop(None, []))

        filters = walk_keys(unicode.lower, filters)
        filters['tag'] = map(r'^[Tt]ag=(.*)', filters.pop('tag=', []))
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
            'samples',
            'annotations',
            'authors',
            'fleiss_kappa',
            'best_cohens_kappa',
        ],
        'search_fields': ['tag__description', ],
    }
    datatable_options_class = AnnotationsSearchOptions

    def get_queryset(self):
        return SerieAnnotation.objects.select_related('series', 'platform', 'tag')

    def apply_queryset_options(self, queryset):
        options = self._get_datatable_options()

        if options['filters']['gse']:
            queryset = queryset.filter(series__gse_name__in=options['filters']['gse'])
        if options['filters']['gpl']:
            queryset = queryset.filter(platform__gpl_name__in=options['filters']['gpl'])
        if options['filters']['tag']:
            queryset = queryset.filter(tag__tag_name__in=options['filters']['tag'])
        if options['filters']['valid']:
            queryset = queryset.filter(best_cohens_kappa=1)

        return super(SeriesAnnotations, self).apply_queryset_options(queryset)


series_annotations = SeriesAnnotations.as_view()


class SampleAnnotations(DatatableView):
    model = SampleAnnotation
    template_name = 'tags/reviews/samples.j2'
    datatable_options = {
        'columns': [
            ('Sample', 'sample__gsm_name'),
            'annotation',
        ]
    }

    def get(self, request, serie_annotation_id):
        self.serie_annotation = get_object_or_404(
            SerieAnnotation.objects.select_related('series'),
            pk=serie_annotation_id
        )
        return super(SampleAnnotations, self).get(request, serie_annotation_id)

    @cached_property
    def sources(self):
        series_tag = self.serie_annotation.series_tag
        return [series_tag] + list(series_tag.validations.filter(ignored=False).order_by('id'))

    def get_queryset(self):
        return SampleAnnotation.objects.select_related('sample') \
                               .filter(serie_annotation=self.serie_annotation)

    def get_context_data(self, **kwargs):
        context = super(SampleAnnotations, self).get_context_data(**kwargs)
        context['serie_annotation'] = self.serie_annotation
        context['source_ids'] = [s.id for s in self.sources]
        return context

    def _get_datatable_options(self):
        options = super(SampleAnnotations, self)._get_datatable_options()
        options['columns'] = [col for col in options['columns']
                              if not isinstance(col, tuple) or col[1] is not None]
        options['columns'].extend(
            (self.get_source_title(src), None, partial(self.get_extra, src))
            for src in self.sources
        )
        return options

    @staticmethod
    def get_source_title(src):
        if src.created_by:
            return u'%s %s' % (src.created_by.first_name, src.created_by.last_name)
        else:
            return u'?'

    def get_extra(self, src, instance, *args, **kwargs):
        if not hasattr(self, 'extra_data'):
            st = self.sources[0]
            sample_annotations = st.sample_tags.values_list('sample_id', 'annotation')
            self.extra_data = {
                (SeriesTag, st.pk, sample_id): annotation
                for sample_id, annotation in sample_annotations
            }
            sample_validations = SampleValidation.objects \
                .filter(serie_validation__in=self.sources[1:]) \
                .values_list('serie_validation', 'sample_id', 'annotation')
            self.extra_data.update({
                (SerieValidation, sv, sample_id): annotation
                for sv, sample_id, annotation in sample_validations
            })

        return self.extra_data[src.__class__, src.pk, instance.sample_id] or ''


sample_annotations = SampleAnnotations.as_view()


def ignore(request, serie_validation_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    sv = get_object_or_404(SerieValidation, pk=serie_validation_id)
    sv.ignored = True
    sv.save()
    validation_workflow.delay(sv.pk, is_new=False)
    return redirect('sample_annotations', sv.series_tag.canonical.id)
