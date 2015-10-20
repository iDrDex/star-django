import json
from itertools import groupby

import jinja2
from django_jinja import library
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe


@library.filter(name='json')
def _json(value):
    if isinstance(value, QuerySet):
        value = list(value)
    return mark_safe(json.dumps(value))


@library.global_function
@jinja2.contextfunction
def replace_get(context, **kwargs):
    request = context.get('request')
    query = request.GET.copy()
    for param in kwargs:
        query.pop(param, None)
    query.update(kwargs)
    return '%s?%s' % (request.path, query.urlencode())


@library.filter
def index(value, attribute):
    res = groupby(value, key=lambda o: getattr(o, attribute)[0].upper())
    return [(key, list(group)) for key, group in res]
