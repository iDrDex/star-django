from django.http import JsonResponse
from tags.models import SampleAnnotation
from funcy import partial, walk_keys
from cacheops import FileCache
file_cache = FileCache('/tmp/cacheops_sample_annotations')


KEYS = {
    'serie_annotation__tag__tag_name': 'tag_name',
    'serie_annotation__tag_id': 'tag_id',
    'serie_annotation__tag__concept_full_id': 'tag_concept_full_id',
    'serie_annotation__series__gse_name': 'gse_name',
    'serie_annotation__series_id': 'serie_id',
    'serie_annotation_id': 'serie_annotation_id',
    'sample__gsm_name': 'gsm_name',
    'sample_id': 'sample_id',
    'sample__platform__gpl_name': 'gpl_name',
    'sample__platform_id': 'platform_id',
    'annotation': 'annotation',
}


@file_cache.cached_view(timeout=60 * 60)
def samples_annotations(request):
    data = map(
        partial(walk_keys, KEYS),
        SampleAnnotation.objects.values(*KEYS).prefetch_related(
            'sample',
            'sample__platform',
            'serie_annotation__tag',
        ).iterator())

    return JsonResponse(data, safe=False, content_type='application/octet-stream')
