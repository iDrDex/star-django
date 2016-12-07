import re
from operator import itemgetter
from collections import defaultdict

from funcy import distinct, imapcat, join, keep, silent, split, map
from handy.decorators import render_to, paginate
from handy.utils import get_or_none

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.forms import ModelForm, ValidationError, HiddenInput
from django.shortcuts import redirect, get_object_or_404

from core.aggregations import ArrayAgg, ArrayConcatUniq, ArrayLength
from core.decorators import block_POST_for_incompetent
from legacy.models import Series
from .models import Tag, SeriesTag


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
            qs = qs.filter(id__in=include_series)
        else:
            message = 'No series annotated with %s.' \
                % (q_tags[0] if len(q_tags) == 1 else 'all these tags simultaneously')
            messages.warning(request, message)
            return {'series': []}
    if exclude_tags:
        exclude_series = join(tag_series[t] for t in exclude_tags)
        qs = qs.exclude(id__in=exclude_series)

    series_ids = qs.values_list('id', flat=True)
    tags = distinct(imapcat(serie_tags, series_ids), key=itemgetter('id'))
    # TODO: do not hide excluded tags

    data = qs.aggregate(samples=Sum('samples_count'),
                        platforms=ArrayLength(ArrayConcatUniq('platforms')),
                        species=ArrayAgg('specie'))
    samples = data['samples']
    platforms = data['platforms']
    species = set(data['species'])
    species.remove('')

    return {
        'series': qs,
        'tags': tags,
        'serie_tags': serie_tags,
        'samples': samples,
        'platforms': platforms,
        'species': species,
    }


def _parse_query(q):
    tags, words = split(r'^tag:', q.split())
    tags = map(r'^tag:(.*)', tags)
    return ' '.join(words), tags


@login_required
@render_to()
def tag_control(request):
    return {
        'tags': Tag.objects.filter(is_active=True).order_by('tag_name')
    }


@login_required
@block_POST_for_incompetent
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
@block_POST_for_incompetent
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
        'tag': tag,
        'stats': tag.get_stats(),
        'form': form
    }

@transaction.atomic
def save_tag(request, form):
    tag = form.save(commit=False)
    old_tag = Tag.objects.select_for_update().get(pk=tag.pk)
    tag.modified_by_id = request.user.id

    # Check for merge
    merge_target = None
    if tag.tag_name != old_tag.tag_name:
        merge_target = get_or_none(Tag, tag_name=tag.tag_name, is_active=True)
    if merge_target:
        if not request.user.is_staff:
            messages.error(request, "You are not allowed to merge tags.")
            return redirect('tag', tag.pk)

        tag.is_active = False
        tag.save()

        tag.remap_annotations(old_tag.tag_name, tag.tag_name)
        tag.remap_refs(merge_target.pk)
        messages.success(request, 'Merged tag %s to %s' % (old_tag.tag_name, tag.tag_name))
    else:
        tag.save()
        tag.remap_annotations(old_tag.tag_name, tag.tag_name)
        messages.success(request, 'Saved tag %s' % tag.tag_name)

    return redirect(tag_control)


@user_passes_test(lambda u: u.is_staff)
def delete_tag(request, tag_id):
    with transaction.atomic():
        tag = get_object_or_404(Tag, pk=tag_id)
        tag.is_active = False
        tag.modified_by_id = request.user.id
        tag.save()
    messages.success(request, 'Successfully deleted %s tag' % tag.tag_name)
    return redirect(tag_control)


class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = ['tag_name', 'description',
                  'concept_name', 'ontology_id', 'concept_full_id']

    def __init__(self, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        self.fields['concept_name'].widget.attrs['class'] = 'bp_form_complete-all-name'
        self.fields['ontology_id'].widget = HiddenInput()
        self.fields['concept_full_id'].widget = HiddenInput()

    def clean_tag_name(self):
        tag_name = self.cleaned_data['tag_name']
        if ' ' in tag_name:
            raise ValidationError('Spaces are not allowed in tag names, use underscores instead.')
        elif not re.search(r'^[a-zA-Z]\w+$', tag_name):
            raise ValidationError('Wrong tag name format.')
        return tag_name

    def clean(self):
        clean_data = super(TagForm, self).clean()
        if 'tag_name' in clean_data and not self.instance.pk:
            if Tag.objects.filter(tag_name=clean_data['tag_name'], is_active=True).exists():
                self.add_error('tag_name',
                               'Tag with name "%s" already exists' % clean_data['tag_name'])


# Data fetching utils

def search_series_qs(query_string):
    if query_string:
        return Series.objects.extra(
            select={'rank': "ts_rank(tsv, plainto_tsquery('english', %s))"},
            select_params=[query_string],
            where=["plainto_tsquery('english', %s) @@ tsv"],
            params=[query_string],
            order_by=['-rank', 'id']
        )
    else:
        return Series.objects.all()


def series_tags_data():
    pairs = SeriesTag.objects.filter(tag__is_active=True) \
                     .values_list('series_id', 'tag_id', 'tag__tag_name').distinct()

    serie_tags = defaultdict(list)
    tag_series = defaultdict(set)
    tag_ids = {}
    for serie_id, tag_id, tag_name in pairs:
        tag_ids[tag_name.lower()] = tag_id
        serie_tags[serie_id].append({'id': tag_id, 'name': tag_name})
        tag_series[tag_id].add(serie_id)

    return serie_tags, tag_series, tag_ids
