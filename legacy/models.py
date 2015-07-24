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

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name


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


class SeriesAttribute(models.Model):
    series = models.ForeignKey(Series, blank=True, null=True)
    attribute_value = models.TextField(blank=True)
    attribute_name = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'series_attribute'


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

    agreed = models.IntegerField(blank=True, null=True)
    fleiss_kappa = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'series_tag'


class Sample(models.Model):
    series = models.ForeignKey('Series', blank=True, null=True)
    platform = models.ForeignKey(Platform, blank=True, null=True)
    gsm_name = models.TextField(blank=True)
    deleted = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sample'


class SampleAttribute(models.Model):
    sample = models.ForeignKey(Sample, blank=True, null=True)
    attribute_value = models.TextField(blank=True)
    attribute_name = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = 'sample_attribute'


class SampleTag(models.Model):
    sample = models.ForeignKey(Sample, blank=True, null=True)
    series_tag = models.ForeignKey('SeriesTag', blank=True, null=True, related_name='sample_tags')
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
