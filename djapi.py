"""
Principles:
- library not framework (helpers + decorators)
- reuse django (i.e. validation)
    - when impossible to reuse, mimic it
- do not hide intentions
    - the less abstraction the better (.json() instead of .response())

DWIM, practicality
"""

import six
import json as _json
from funcy import decorator, is_iter, chain, select_values
from funcy import cached_property, rcompose, memoize, iffy, isa, partial, walk_values, flip

import django
from django.conf import settings
from django.core.exceptions import FieldError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet, F
from django.http import HttpResponse, HttpResponseNotAllowed
from django.views import defaults
from django.shortcuts import _get_queryset
from django.utils.module_loading import import_string


class SmarterJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, QuerySet) or is_iter(o):
            return list(o)
        else:
            return super(SmarterJSONEncoder, self).default(o)

def json(data, **kwargs):
    # Allow response pass through, e.g. error
    if isinstance(data, HttpResponse):
        return data
    # Pretty print in debug mode
    if settings.DEBUG:
        json_data = _json.dumps(data, cls=SmarterJSONEncoder, indent=4)
    else:
        json_data = _json.dumps(data, cls=SmarterJSONEncoder, separators=(',', ':'))
    # Set Content Type: application/json by default
    kwargs.setdefault('content_type', 'application/json')
    return HttpResponse(json_data, **kwargs)

def json_error(status, message):
    return json({'detail': message}, status=status)


# Querysets
# TODO: review this in Django 1.9+, there is no built-in QuerySet sublclasses
@memoize  # noqa
def _extend_queryset_class(base):
    class _QuerySet(base):
        @cached_property
        def _mappers(self):
            return []

        if django.VERSION >= (1, 9):
            def _clone(self, **kwargs):
                clone = base._clone(self, **kwargs)
                clone._mappers = self._mappers
                return clone

        else:
            def _clone(self, klass=None, setup=False, **kwargs):
                if klass and not klass.__name__.startswith('API'):
                    klass = _extend_queryset_class(klass)
                clone = base._clone(self, klass=klass, setup=setup, **kwargs)
                clone._mappers = self._mappers
                return clone

        def _fetch_all(self):
            # This thing appears in Django 1.9.
            # In Djangos 1.9 and 1.10 both calls mean the same.
            # Starting from Django 1.11 .iterator() uses chunked fetch
            # while ._fetch_all() stays with bare _iterable_class.
            if hasattr(self, '_iterable_class'):
                it = self._iterable_class(self)
            else:
                it = self.iterator()
            self._result_cache = map(rcompose(*self._mappers), it)

            # Fill in the rest
            base._fetch_all(self)

        def map(self, func):
            clone = self._clone()
            clone._mappers.append(func)
            return clone

        def map_types(self, types, func):
            return self.map(partial(walk_values, iffy(isa(types), func)))

        def values(self, *fields, **expressions):
            """
            Extended version supporting renames:
                .values('id', 'name', author__name='author')
            """
            renames = select_values(isa(six.string_types), expressions)
            if not renames:
                return base.values(self, *fields, **expressions)
            elif django.VERSION >= (1, 11):
                rename_expressions = walk_values(F, renames)
                expressions.update(rename_expressions)
                return base.values(self, *fields, **expressions)
            else:
                f_to_name = flip(renames)
                rename = lambda d: {f_to_name.get(k, k): v for k, v in d.items()}
                return base.values(self, *chain(fields, f_to_name)).map(rename)

        # TODO: .values_list_but() ?
        def values_but(self, *exclude):
            exclude = set(exclude)
            attnames = {f.name: f.attname for f in self.model._meta.fields}
            known = set(attnames) | set(attnames.values()) | {'pk'}
            unknown = exclude - known
            if unknown:
                raise FieldError("Cannot resolve keyword%(p)s %(unknown)s into field%(p)s. "
                                 "Choices are: %(known)s." % {
                                     'unknown': ', '.join(sorted(unknown)),
                                     'known': ', '.join(sorted(known)),
                                     'p': 's' if len(unknown) > 1 else '',
                                 })

            fields = [att for name, att in attnames.items() if not {name, att} & exclude]
            return self.values(*fields)

        def values_add(self, *fields, **expressions):
            return self.values(*(self._fields + fields), **expressions)

    _QuerySet.__name__ = 'API' + base.__name__
    return _QuerySet

def queryset(qs):
    qs = _get_queryset(qs)
    qs.__class__ = _extend_queryset_class(qs.__class__)
    return qs

def exclude_fields(qs, exclude):
    raise NotImplementedError

def rename_keys(data, renames):
    return [{renames.get(k, k): v for k, v in d.items()} for d in data]

def get_or_404(qs, *args, **kwargs):
    qs = _get_queryset(qs)
    try:
        return qs.get(*args, **kwargs)
    except qs.model.DoesNotExist as e:
        return json_error(404, e.args[0])


@decorator
def catch(call, exception, status=500):
    try:
        return call()
    except exception as e:
        return json_error(status, e.args[0])

def paginate(request, qs, per_page=None):
    offset = request.GET.get('offset', 0)
    limit = request.GET.get('limit', per_page)
    # TODO: better error message
    if limit is None:
        return json_error(400, 'limit parameter is required')
    try:
        offset = int(offset)
        limit = int(limit)
    except ValueError:
        return json_error(400, 'Bad value for offset or limit parameter')

    count = qs.count()
    page = qs[offset:offset + limit]

    uri = _request_uri(request)
    if limit == per_page:
        uri_template = uri + '?offset=%d'
    else:
        uri_template = uri + '?limit=%d&offset=%%d' % limit
    return {
        'count': count,
        'next': uri_template % (offset + limit) if offset + limit < count else None,
        'previous': uri_template % (offset - limit) if offset > limit else None,
        'results': page,
    }

def _request_uri(request):
    return '{scheme}://{host}{path}'.format(
        scheme=request.scheme, host=request.get_host(), path=request.path)


# View helpers

@decorator
def validate(call, form=None):
    # TODO: support json input, autodetect by content type
    aform = form(call.request.POST)
    if not aform.is_valid():
        return json({'detail': 'Validation failed', 'errors': aform._errors}, status=400)

    return call(aform.save(commit=False) if hasattr(aform, 'save') else aform.cleaned_data)

# Changed from method to property
if django.VERSION >= (1, 10):
    is_authenticated = lambda user: user.is_authenticated
else:
    is_authenticated = lambda user: user.is_authenticated()

def attempt_auth(request):
    if is_authenticated(request.user):
        return True
    hooks = getattr(settings, 'DJAPI_AUTH', [])
    for hook in hooks:
        import_string(hook)(request)
        if is_authenticated(request.user):
            return True
    else:
        return False

@decorator
def user_passes_test(call, test, message=None, status=403):
    attempt_auth(call.request)
    if test(call.request.user):
        return call()
    else:
        return json_error(status, message or 'Permission required')

auth_required = user_passes_test(is_authenticated, status=401, message='Authorization required')


# Routing

def get_post(get, post):
    def view(request, *args, **kwargs):
        if request.method == 'GET':
            return get(request, *args, **kwargs)
        elif request.method == 'POST':
            return post(request, *args, **kwargs)
        else:
            return HttpResponseNotAllowed(['GET', 'POST'])
    return view


# TODO: think if this is a good idea
def make_page_not_found(uri_prefix):
    def page_not_found(request, exception=None, template_name='404.html'):
        if uri_prefix and not request.path.startswith(uri_prefix):
            # TODO: pass exception for newer djangos
            return defaults.page_not_found(request, template_name=template_name)
        try:
            message = exception.args[0]
        except (AttributeError, IndexError):
            message = 'Not found'
        return json_error(404, message)
    return page_not_found

page_not_found = make_page_not_found('')
