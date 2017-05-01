from funcy import group_by, cached_property, partial, walk_keys, map
from datatableview.views import DatatableView
from datatableview.utils import DatatableOptions
from handy.decorators import render_to, paginate
from handy.utils import get_or_none

from django.http import HttpResponseForbidden, Http404
from django.forms import ModelForm, CharField
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
        # Try normally named field
        if not options['search']:
            options['search'] = query.get('search', '').strip()

        filters = group_by(r'^(GSE|GPL|[Tt]ag=|valid|novalid)', options['search'].split())
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
        if options['filters']['novalid']:
            queryset = queryset.exclude(best_cohens_kappa=1)

        return super(SeriesAnnotations, self).apply_queryset_options(queryset)

    def get_context_data(self, **kwargs):
        context = super(SeriesAnnotations, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            context['snapshot'] = get_or_none(Snapshot, author=self.request.user, frozen=False)
        return context

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


# Snapshots

import urllib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from tags.models import Snapshot


@login_required
@require_POST
def snapshot(request):
    action = request.POST.get('action')
    search = request.POST.get('search')
    next_url = '%s?%s' % (request.POST.get('next'), urllib.urlencode({'search': search}))

    if action not in {'make', 'add', 'remove', 'delete', 'freeze'}:
        return HttpResponseForbidden('Unknown action %s' % action)

    if action == 'make':
        snap, _ = Snapshot.objects.get_or_create(author=request.user, frozen=False)
        messages.success(request, "Created an empty snapshot for you. "
                                  "Now add searches to it.")
        return redirect(next_url)

    snap = get_or_none(Snapshot, author=request.user, frozen=False)
    if not snap:
        return HttpResponseForbidden('No unfrozen snapshot found')

    if action == 'add':
        if not search:
            messages.error(request, "Can't add all the annotations to snapshot. "
                                    "Make some search or go into any annotation.")
        else:
            added, message = snap.add(search, get_search_qs(request))
            if added:
                snap.save()
                messages.success(request, 'Added "%s" to snaphot' % search)
            else:
                messages.warning(request, message)
    elif action == 'remove':
        removed, message = snap.remove(search)
        if removed:
            snap.save()
        elif message:
            messages.error(request, message)
    elif action == 'delete':
        snap.delete()
    elif action == 'freeze':
        snap.freeze()
        return redirect('snapshot_detail', snap.id)

    return redirect(next_url)


def get_search_qs(request):
    view = SeriesAnnotations()
    view._datatable_options = view.datatable_options_class(
        view.get_model(), request.POST,
        **SeriesAnnotations.datatable_options)
    view.request = request
    qs = view.get_object_list()
    return qs


class ReviewSnapshot(SeriesAnnotations):
    template_name = 'snapshots/review.j2'

    def get_queryset(self):
        snapshot = get_or_none(Snapshot, author=self.request.user, frozen=False)
        if not snapshot:
            return SerieAnnotation.objects.none()
        return super(ReviewSnapshot, self).get_queryset() \
                                          .filter(id__in=snapshot.metadata.get('ids', []))
review_snapshot = login_required(ReviewSnapshot.as_view())


@render_to('snapshots/detail.j2')
def snapshot_detail(request, snap_id):
    snap = get_object_or_404(Snapshot, pk=snap_id)
    if not snap.frozen:
        if snap.author == request.user:
            return redirect('review_snapshot')
        else:
            raise Http404
    form = None

    if snap.author == request.user:
        if request.method == 'POST':
            form = SnapshotForm(request.POST, instance=snap)
            if form.is_valid():
                form.save()
                messages.success(request, "Updated snapshot description")
                return redirect('snapshot_detail', snap_id)
        else:
            form = SnapshotForm(instance=snap)

    return {
        'snapshot': snap,
        'form': form,
    }


class SnapshotForm(ModelForm):
    class Meta:
        model = Snapshot
        fields = ['title', 'description']

    title = CharField()


from funcy import first, where

def snapshot_file(request, snap_id, format):
    snap = get_object_or_404(Snapshot, pk=snap_id)
    f = first(where(snap.files, format=format))
    return redirect(f.url)


@login_required
@render_to('snapshots/list.j2')
@paginate('snapshots', 10)
def my_snapshots(request):
    return {'snapshots': Snapshot.objects.filter(author=request.user).order_by('-frozen_on')}
