from operator import itemgetter
from collections import defaultdict

from funcy import distinct, imapcat, join, str_join
from handy.decorators import render_to, paginate

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404

from legacy.models import Tag, SampleTag, SeriesTag
from core.utils import login_required
from .models import SampleValidation
from .data import get_series_columns, SQLQuerySet


@render_to()
@paginate('series', 10)
def search(request):
    q = request.GET.get('q')
    exclude_tags = request.GET.getlist('exclude_tags')
    serie_tags, tag_series = series_tags_data()

    if q:
        qs = search_series_qs(q)
        series_ids = qs.values_list('series_id', flat=True)
        tags = distinct(imapcat(serie_tags, series_ids), key=itemgetter('id'))

        if exclude_tags:
            exclude_series = join(tag_series[int(t)] for t in exclude_tags)
            qs = qs.where('series_id not in (%s)' % str_join(',', exclude_series))
    else:
        qs = None
        tags = None

    return {
        'series': qs,
        'tags': tags,
        'serie_tags': serie_tags,
    }


@login_required
@render_to()
def tag_control(request):
    return {
        'tags': Tag.objects.order_by('tag_name')
    }

@login_required
@render_to()
def tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            tag = form.save(commit=False)
            save_tag(tag)
            messages.success(request, 'Saved tag %s' % tag.tag_name)
            return redirect('tag', tag_id)
    else:
        form = TagForm(instance=tag)

    return {
        'form': form
    }

@transaction.atomic('legacy')
def save_tag(tag):
    old_tag = Tag.objects.select_for_update().get(pk=tag.pk)
    tag.save()

    if tag.tag_name != old_tag.tag_name:
        SampleTag.objects.filter(series_tag__tag=tag, annotation=old_tag.tag_name) \
                 .update(annotation=tag.tag_name)
        SampleValidation.objects.filter(serie_validation__tag=tag, annotation=old_tag.tag_name) \
                        .update(annotation=tag.tag_name)


from django.forms import ModelForm

class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = ['tag_name', 'description']


# Data fetching utils

def search_series_qs(query_string):
    sql = """
             select S.gse_name, {}, ts_rank_cd(doc, q) as rank
             from series_view SV join series S on (SV.series_id = S.id)
             , plainto_tsquery('english', %s) as q
             where doc @@ q order by rank desc
          """.format(', '.join(get_series_columns()))
    return SQLQuerySet(sql, (query_string,), server='legacy')


def series_tags_data():
    pairs = SeriesTag.objects.values_list('series_id', 'tag_id', 'tag__tag_name').distinct()

    serie_tags = defaultdict(list)
    tag_series = defaultdict(set)
    for serie_id, tag_id, tag_name in pairs:
        serie_tags[serie_id].append({'id': tag_id, 'name': tag_name})
        tag_series[tag_id].add(serie_id)

    return serie_tags, tag_series
