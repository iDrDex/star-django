import re

import boto

from django.conf import settings
from django.utils.encoding import force_unicode


def upload(desc):
    assert {'bucket', 'name', 'data'} <= set(desc)

    bucket = _get_bucket(desc['bucket'])
    key_name = clean_key_name(desc['name'])
    key = bucket.new_key(key_name)
    key.set_contents_from_string(desc['data'])

    return dict(bucket=desc['bucket'], key=key_name, name=desc['name'], size=len(desc['data']))


def download_as_string(desc):
    bucket = _get_bucket(desc['bucket'])
    key = bucket.get_key(desc['key'], validate=False)
    return key.get_contents_as_string()


def download_to_filename(desc, to_filename):
    bucket = _get_bucket(desc['bucket'])
    key = bucket.get_key(desc['key'], validate=False)
    key.get_contents_to_filename(to_filename)


def remove_files(bucket_name, key_names):
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
