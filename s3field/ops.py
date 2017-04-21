import re
from thread import start_new_thread

import boto
import pandas as pd

from django.conf import settings
from django.utils.encoding import force_unicode
from cacheops import file_cache


def upload(desc, lazy=False):
    assert {'bucket', 'name', 'data'} <= set(desc)

    res = desc.copy()
    del res['data']
    res['size'] = len(desc['data'])
    res['key'] = clean_key_name(desc['name'])

    if lazy:
        start_new_thread(_upload, (res['bucket'], res['key'], desc['data']))
    else:
        _upload(res['bucket'], res['key'], desc['data'])

    return res


def _upload(bucket_name, key_name, data):
    # Cache to avoid download to same instance
    download_as_string.key(bucket_name, key_name).set(data)
    # Upload
    bucket = _get_bucket(bucket_name)
    key = bucket.new_key(key_name)
    key.set_contents_from_string(data)


@file_cache.cached
def download_as_string(bucket_name, key_name):
    bucket = _get_bucket(bucket_name)
    key = bucket.get_key(key_name, validate=False)
    return key.get_contents_as_string()


def download_to_filename(desc, to_filename):  # flaw: never used
    bucket = _get_bucket(desc['bucket'])
    key = bucket.get_key(desc['key'], validate=False)
    key.get_contents_to_filename(to_filename)


def remove_files(bucket_name, key_names):  # flaw: never used
    if not key_names:
        return
    _get_bucket(bucket_name).delete_keys(key_names)


def _get_bucket(bucket_name):
    conn = boto.connect_s3(aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                           is_secure=False)
    return conn.get_bucket(bucket_name)


MAX_KEY_LEN = 1024

def clean_key_name(key_name):
    """
    Clean the key_name to the form suitable to be used as an Amazon S3 key
    """
    key_name = force_unicode(key_name, errors='ignore')
    # Remove backslashes and space
    key_name = re.sub(r'[ \\_]+', '_', key_name)
    # Remove double dots and slashes
    key_name = re.sub(r'([./])\1+', r'\1', key_name)
    return key_name[:MAX_KEY_LEN].strip(u'._/')


def frame_dumps(df):
    return df.to_json(orient='split')

def frame_loads(s):
    return pd.io.json.read_json(s, orient='split')
