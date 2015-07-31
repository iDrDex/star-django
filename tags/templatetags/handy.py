import json

import jinja2
from django_jinja import library
from django.db.models.query import QuerySet


@library.filter(name='json')
def _json(value):
    if isinstance(value, QuerySet):
        value = list(value)
    return json.dumps(value)


@library.global_function
@jinja2.contextfunction
def replace_get(context, **kwargs):
    request = context.get('request')
    query = request.GET.copy()
    query.update(kwargs)
    return '%s?%s' % (request.path, query.urlencode())
