import json
import math

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
    def human_size(self):
        if self['size'] == 0:
            return '0b'
        i = int(math.log(self['size'], 1024))
        return '%d%s' % (math.ceil(self['size'] / 1024 ** i), ['b', 'kb', 'mb', 'gb', 'tb'][i])

    @cached_property
    def frame(self):
        # TODO: cache this in file locally
        return frame_loads(ops.download_as_string(self))


class S3Field(models.TextField):
    """
    A field representing an attachment stored in Amazon S3.
    """
    def __init__(self, verbose_name=None, name=None, make_name=None, **kwargs):
        self.make_name = make_name
        models.Field.__init__(self, verbose_name, name, **kwargs)

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

    def contribute_to_class(self, cls, name, **kwargs):
        super(S3Field, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, 'upload_%s' % self.name, func_partial(_upload_FIELD, field=self))

    def _get_bucket(self):
        key = '%s.%s.%s' % (self.model._meta.app_label, self.model._meta.model_name, self.name)
        try:
            return settings.S3_BUCKETS[key]
        except KeyError:
            raise ImproperlyConfigured('Please specify S3 bucket for %s' % key)


def _upload_FIELD(self, desc, field=None):  # noqa
    # NOTE: only dataframes for now
    assert isinstance(desc, pd.DataFrame)
    desc = {
        'bucket': field._get_bucket(),
        'name': field.make_name(self),
        'data': frame_dumps(desc),
    }
    setattr(self, field.attname, Resource(ops.upload(desc)))


def frame_dumps(df):
    return df.to_json(orient='split')

def frame_loads(s):
    return pd.io.json.read_json(s, orient='split')
