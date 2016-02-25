import re
from operator import itemgetter
from collections import defaultdict

from funcy import distinct, imapcat, join, str_join, keep, silent, split, map
from handy.decorators import render_to, paginate

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.forms import ModelForm, ValidationError
from django.shortcuts import redirect, get_object_or_404

from legacy.models import Tag, SeriesTag
from .data import get_series_columns, SQLQuerySet


@render_to()
@paginate('series', 10)
def search(request):
    q = request.GET.get('q')
    if not q:
        return {'series': None}

    exclude_tags = keep(silent(int), request.GET.getlist('exclude_tags'))
    serie_tags, tag_series, tag_ids = series_tags_data()

    q_string, q_tags = _parse_query(q)
    q_tags, wrong_tags = split(lambda t: t.lower() in tag_ids, q_tags)
    if wrong_tags:
        message = 'Unknown tag%s %s.' % ('s' if len(wrong_tags) > 1 else '', ', '.join(wrong_tags))
        messages.warning(request, message)
    if not q_string and not q_tags:
        return {'series': None}

    qs = search_series_qs(q_string)
    if q_tags:
        q_tag_ids = keep(tag_ids.get(t.lower()) for t in q_tags)
        include_series = reduce(set.intersection, (tag_series[t] for t in q_tag_ids))
        if include_series:
            qs = qs.where('series_id in (%s)' % str_join(',', include_series))
        else:
            message = 'No series annotated with %s.' \
                % (q_tags[0] if len(q_tags) == 1 else 'all these tags simultaneously')
            messages.warning(request, message)
            return {'series': []}
    if exclude_tags:
        exclude_series = join(tag_series[t] for t in exclude_tags)
        qs = qs.where('series_id not in (%s)' % str_join(',', exclude_series))

    series_ids = qs.values_list('series_id', flat=True)
    tags = distinct(imapcat(serie_tags, series_ids), key=itemgetter('id'))

    return {
        'series': qs,
        'tags': tags,
        'serie_tags': serie_tags,
    }

def _parse_query(q):
    tags, words = split(r'^tag:', q.split())
    tags = map(r'^tag:(.*)', tags)
    return ' '.join(words), tags


@login_required
@render_to()
def tag_control(request):
    return {
        'tags': Tag.objects.order_by('tag_name')
    }


@login_required
@render_to('tags/tag.j2')
def create_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.created_by_id = tag.modified_by_id = request.user.id
            tag.save()
            messages.success(request, 'Saved tag %s' % tag.tag_name)
            return redirect(tag_control)
    else:
        form = TagForm()

    return {
        'title': 'Create tag',
        'form': form
    }


@login_required
@render_to()
def tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            return save_tag(request, form)
    else:
        form = TagForm(instance=tag)

    return {
        'title': 'Edit tag',
        'stats': tag.get_stats(),
        'form': form
    }

@transaction.atomic
def save_tag(request, form):
    tag = form.save(commit=False)
    old_tag = Tag.objects.select_for_update().get(pk=tag.pk)
    tag.modified_by_id = request.user.id
    tag.save()

    tag.remap_annotations(old_tag.tag_name, tag.tag_name)

    messages.success(request, 'Saved tag %s' % tag.tag_name)
    return redirect(tag_control)


class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = ['tag_name', 'description']

    def clean_tag_name(self):
        tag_name = self.cleaned_data['tag_name']
        if ' ' in tag_name:
            raise ValidationError('Spaces are not allowed in tag names, use underscores instead.')
        elif not re.search(r'^[a-zA-Z]\w+$', tag_name):
            raise ValidationError('Wrong tag name format.')
        return tag_name


# Data fetching utils

def search_series_qs(query_string):
    if query_string:
        sql = """
                 select S.gse_name, {}, ts_rank_cd(doc, q) as rank
                 from series_view SV join series S on (SV.series_id = S.id)
                 , plainto_tsquery('english', %s) as q
                 where doc @@ q order by rank desc, S.id
              """.format(', '.join(get_series_columns()))
        params = (query_string,)
    else:
        # HACK: we use `where true` here to make SQLQuerySet.where() to work
        sql = """
                 select S.gse_name, {}
                 from series_view SV join series S on (SV.series_id = S.id)
                 where true order by S.id
              """.format(', '.join(get_series_columns()))
        params = ()
    return SQLQuerySet(sql, params)


def series_tags_data():
    pairs = SeriesTag.objects.values_list('series_id', 'tag_id', 'tag__tag_name').distinct()

    serie_tags = defaultdict(list)
    tag_series = defaultdict(set)
    tag_ids = {}
    for serie_id, tag_id, tag_name in pairs:
        tag_ids[tag_name.lower()] = tag_id
        serie_tags[serie_id].append({'id': tag_id, 'name': tag_name})
        tag_series[tag_id].add(serie_id)

    return serie_tags, tag_series, tag_ids
