from __future__ import unicode_literals

from django.db import models


class AuthUser(models.Model):
    first_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    email = models.CharField(max_length=512, blank=True)
    password = models.CharField(max_length=512, blank=True)
    registration_key = models.CharField(max_length=512, blank=True)
    reset_password_key = models.CharField(max_length=512, blank=True)
    registration_id = models.CharField(max_length=512, blank=True)

    class Meta:
        managed = False
        db_table = 'auth_user'


class Platform(models.Model):
    gpl_name = models.TextField(blank=True)
    scopes = models.CharField(max_length=512, blank=True)
    identifier = models.CharField(max_length=512, blank=True)
    datafile = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'platform'


class Tag(models.Model):
    tag_name = models.CharField(unique=True, max_length=512, blank=True)
    description = models.CharField(max_length=512, blank=True)
    is_active = models.CharField(max_length=1, blank=True)
    created_on = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(AuthUser, db_column='created_by', blank=True, null=True,
                                   related_name='tags')
    modified_on = models.DateTimeField(blank=True, null=True)
    modified_by = models.ForeignKey(AuthUser, db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    class Meta:
        managed = False
        db_table = 'tag'


class Series(models.Model):
    gse_name = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'series'


class SeriesTag(models.Model):
    series = models.ForeignKey(Series, blank=True, null=True)
    platform = models.ForeignKey(Platform, blank=True, null=True)
    tag = models.ForeignKey('Tag', blank=True, null=True)
    header = models.CharField(max_length=512, blank=True)
    regex = models.CharField(max_length=512, blank=True)
    show_invariant = models.CharField(max_length=1, blank=True)
    is_active = models.CharField(max_length=1, blank=True, default='T')
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey(AuthUser, db_column='created_by', blank=True, null=True,
                                   related_name='serie_annotations')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey(AuthUser, db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    class Meta:
        managed = False
        db_table = 'series_tag'


class Sample(models.Model):
    series = models.ForeignKey('Series', blank=True, null=True)
    platform = models.ForeignKey(Platform, blank=True, null=True)
    gsm_name = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'sample'


class SampleTag(models.Model):
    sample = models.ForeignKey(Sample, blank=True, null=True)
    series_tag = models.ForeignKey('SeriesTag', blank=True, null=True)
    annotation = models.TextField(blank=True)
    is_active = models.CharField(max_length=1, blank=True, default='T')
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey(AuthUser, db_column='created_by', blank=True, null=True,
                                   related_name='sample_annotations')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey(AuthUser, db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    class Meta:
        managed = False
        db_table = 'sample_tag'


class LegacyRouter(object):
    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'legacy':
            return 'legacy'
    db_for_read = db_for_write

    def allow_relation(self, obj1, obj2, **hints):
        is_legacy = lambda o: o._meta.app_label == 'legacy'
        return is_legacy(obj1) == is_legacy(obj2)
