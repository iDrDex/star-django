import json
import math
import gzip
import zlib
from cStringIO import StringIO

from funcy import cached_property, func_partial
import pandas as pd

from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.db import models

from . import ops


class Resource(dict):
    """A resource value"""
    def __init__(self, data):
        dict.__init__(self, data)
        assert {'bucket', 'key', 'name', 'size'} <= set(self)

    @property
    def url(self):
        return "http://{bucket}.s3.amazonaws.com/{key}".format(**self)

    @property
    def human_size(self):
        if self['size'] == 0:
            return '0b'
        i = int(math.log(self['size'], 1024))
        return '%d%s' % (math.ceil(self['size'] / 1024 ** i), ['b', 'kb', 'mb', 'gb', 'tb'][i])

    @cached_property
    def frame(self):
        return ops.frame_loads(self._raw())

    def _raw(self):
        blob = ops.download_as_string(self['bucket'], self['key'])
        if self.get('compressed') in {True, 'zlib'}:
            blob = zlib.decompress(blob)
        elif self.get('compressed') == 'gzip':
            blob = gzip_decompress(blob)
        return blob
    raw = cached_property(_raw)

    def open(self):
        return StringIO(self.raw)


class S3BaseField(models.TextField):
    """
    A base field representing an attachment stored in Amazon S3.
    """
    def __init__(self, verbose_name=None, name=None, make_name=None, compress=False, **kwargs):
        self.make_name = make_name
        self.compress = compress
        models.Field.__init__(self, verbose_name, name, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super(S3BaseField, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, 'upload_%s' % self.name, func_partial(_upload_FIELD, field=self))

    def _get_bucket(self):
        key = '%s.%s.%s' % (self.model._meta.app_label, self.model._meta.model_name, self.name)
        try:
            return settings.S3_BUCKETS[key]
        except KeyError:
            raise ImproperlyConfigured('Please specify S3 bucket for %s' % key)


class S3Field(S3BaseField):
    """
    A field representing a single attachment stored in Amazon S3.
    """
    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, Resource):
            return value

        if isinstance(value, basestring):
            return Resource(json.loads(value))

        raise ValidationError('Wrong resource description')

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return None
        return Resource(json.loads(value))

    def get_prep_value(self, value):
        if value is None:
            return None
        return json.dumps(value)

    def _get_bucket(self):
        key = '%s.%s.%s' % (self.model._meta.app_label, self.model._meta.model_name, self.name)
        try:
            return settings.S3_BUCKETS[key]
        except KeyError:
            raise ImproperlyConfigured('Please specify S3 bucket for %s' % key)


class S3MultiField(S3BaseField):
    def __init__(self, verbose_name=None, name=None, **kwargs):
        if kwargs.get('null') or kwargs.get('default', list) is not list:
            raise ValueError('S3MultiField is always not null and defaults to empty list')
        S3BaseField.__init__(self, verbose_name, name, **kwargs)

    def to_python(self, value):
        if isinstance(value, list):
            return value

        if isinstance(value, basestring):
            return map(Resource, json.loads(value))

        raise ValidationError('Wrong resource description')

    def from_db_value(self, value, expression, connection, context):
        return map(Resource, json.loads(value))

    def get_prep_value(self, value):
        return json.dumps(value)


def _upload_FIELD(self, desc, field=None, lazy=False):  # noqa
    if isinstance(desc, pd.DataFrame):
        desc = {'data': ops.frame_dumps(desc)}
    if field.compress in {True, 'zlib'}:
        desc['data'] = zlib.compress(desc['data'])
    elif field.compress == 'gzip':
        desc['data'] = gzip_compress(desc['data'])

    if not desc.get('name'):
        assert field.make_name
        desc['name'] = field.make_name(self)

    desc.update({
        'bucket': field._get_bucket(),
        'compressed': field.compress,
    })
    resource = Resource(ops.upload(desc, lazy=lazy))
    if isinstance(field, S3Field):
        setattr(self, field.attname, resource)
    else:
        getattr(self, field.attname).append(resource)


def gzip_compress(data):
    out = StringIO()
    with gzip.GzipFile(fileobj=out, mode="w") as f:
        f.write(data)
    return out.getvalue()

def gzip_decompress(data):
    with gzip.GzipFile(fileobj=StringIO(data)) as f:
        return f.read()
