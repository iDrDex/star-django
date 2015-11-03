import re
from funcy import silent, without
from handy.decorators import render_to
from datatableview.views import DatatableView

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.forms import ModelForm
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import redirect, get_object_or_404

from core.conf import redis_client
from legacy.models import Analysis, MetaAnalysis
from .tasks import analysis_task


class Index(DatatableView):
    model = Analysis
    template_name = 'analysis/index.j2'
    datatable_options = {
        'columns': [
            'id',
            ('Name', 'analysis_name'),
            ('Case', 'case_query'), ('Control', 'control_query'), ('Modifier', 'modifier_query'),
            ('Series', 'series_count'), ('Platforms', 'platform_count'), ('Samples', 'sample_count')
        ]
    }

    def get_queryset(self):
        return Analysis.objects.exclude(deleted='T').order_by('-id')

index = Index.as_view()


class Detail(DatatableView):
    model = MetaAnalysis
    template_name = 'analysis/detail.j2'
    datatable_options = {
        'hidden_columns': ['id', 'analysis']
    }

    def get(self, request, analysis_id):
        self.analysis_id = analysis_id
        self.analysis = get_object_or_404(Analysis, pk=analysis_id)
        return super(Detail, self).get(request, analysis_id)

    def get_queryset(self):
        return MetaAnalysis.objects.filter(analysis=self.analysis_id)

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)
        context['analysis'] = self.analysis
        return context

detail = Detail.as_view()


def export(request, analysis_id):
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    qs = MetaAnalysis.objects.filter(analysis=analysis)
    fieldnames = without([f.name for f in MetaAnalysis._meta.fields], 'id', 'analysis')
    csv = qs.to_dataframe(fieldnames, index='mygene_sym').to_csv()

    response = HttpResponse(csv, content_type='text/plain')
    filename = re.sub(r'\W+', '-', analysis.analysis_name)
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename
    return response


@render_to()
def frame(request, analysis_id):
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    if not analysis.df:
        raise Http404
    df = analysis.df.frame.drop(['sample_id', 'series_id', 'platform_id'], axis=1)
    return {'analysis': analysis, 'df': df}


@render_to()
def log(request, analysis_id):
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    offset = silent(int)(request.GET.get('offset')) or 0

    log_lines = redis_client.lrange('analysis:%s:log' % analysis_id, offset, -1)
    if request.is_ajax():
        return JsonResponse(log_lines, safe=False)
    else:
        return {'analysis': analysis, 'log_lines': log_lines}


@login_required
@render_to()
def create(request):
    if request.method == 'POST':
        form = AnalysisForm(request.POST)
        if form.is_valid():
            analysis = form.save(commit=False)
            return save_analysis(request, analysis)
    else:
        form = AnalysisForm()

    return {
        'form': form
    }

def save_analysis(request, analysis):
    with transaction.atomic():
        analysis.created_by_id = analysis.modified_by_id = request.user.id
        analysis.save()
    analysis_task.delay(analysis.pk)
    return redirect(log, analysis.pk)


class AnalysisForm(ModelForm):
    class Meta:
        model = Analysis
        fields = ['analysis_name', 'description',
                  'case_query', 'control_query', 'modifier_query', 'min_samples']


@login_required
def rerun(request, analysis_id):
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    if request.GET.get('copy'):
        analysis.pk = None
        analysis.deleted = None
        analysis.created_by_id = analysis.modified_by_id = request.user.id
        analysis.save()
    else:
        analysis.modified_by_id = request.user.id
        analysis.save()
    analysis_task.delay(analysis.pk)
    return redirect(log, analysis.pk)


@login_required
def delete(request, analysis_id):
    with transaction.atomic():
        analysis = get_object_or_404(Analysis, pk=analysis_id)
        analysis.deleted = 'T'
        analysis.save()
    messages.success(request, 'Successfully deleted %s analysis' % analysis.analysis_name)
    return redirect(index)
