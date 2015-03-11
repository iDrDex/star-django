import json

from django_jinja import library
from django.db.models.query import QuerySet


@library.filter(name='json')
def _json(value):
    if isinstance(value, QuerySet):
        value = list(value)
    return json.dumps(value)
