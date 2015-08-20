from funcy import silent
from handy.decorators import render_to, paginate
from datatableview.views import DatatableView

from django.db import transaction
from django.forms import ModelForm
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404

from core.conf import redis_client
from core.utils import login_required
from legacy.models import Analysis, MetaAnalysis
from .tasks import analysis_task


@render_to()
@paginate('analyses', 10)
def index(request):
    return {
        'analyses': Analysis.objects.order_by('-id'),
    }


class Detail(DatatableView):
    model = MetaAnalysis
    template_name = 'analysis/detail.j2'
    datatable_options = {
        'hidden_columns': ['id', 'analysis']
    }

    def get(self, request, analysis_id):
        self.analysis_id = analysis_id
        return super(Detail, self).get(request, analysis_id)

    def get_queryset(self):
        return MetaAnalysis.objects.filter(analysis=self.analysis_id)

detail = Detail.as_view()


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

@transaction.atomic('legacy')
def save_analysis(request, analysis):
    analysis.created_by_id = analysis.modified_by_id = request.user_data['id']
    analysis.save()
    analysis_task.delay(analysis.pk)
    return redirect(log, analysis.pk)


class AnalysisForm(ModelForm):
    class Meta:
        model = Analysis
        fields = ['analysis_name', 'description', 'case_query', 'control_query', 'modifier_query']
