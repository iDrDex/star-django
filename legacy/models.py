from __future__ import unicode_literals

from django.db import models
from django_pandas.managers import DataFrameManager


class AuthUser(models.Model):
    first_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    email = models.CharField(max_length=512, blank=True)
    password = models.CharField(max_length=512, blank=True)
    registration_key = models.CharField(max_length=512, blank=True)
    reset_password_key = models.CharField(max_length=512, blank=True)
    registration_id = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = 'auth_user'

    def __unicode__(self):
        return self.first_name + ' ' + self.last_name


class Platform(models.Model):
    gpl_name = models.TextField(blank=True)
    scopes = models.CharField(max_length=512, blank=True)
    identifier = models.CharField(max_length=512, blank=True)
    datafile = models.TextField(blank=True)

    class Meta:
        db_table = 'platform'


class PlatformProbe(models.Model):
    platform = models.ForeignKey(Platform, blank=True, null=True)
    probe = models.TextField(blank=True)
    mygene_sym = models.TextField(blank=True)
    mygene_entrez = models.IntegerField(blank=True, null=True)

    objects = DataFrameManager()

    class Meta:
        db_table = 'platform_probe'


class Tag(models.Model):
    tag_name = models.CharField(unique=True, max_length=512, blank=True)
    description = models.CharField(max_length=512, blank=True)
    is_active = models.CharField(max_length=1, blank=True, default='T')
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey('auth.User', db_column='created_by', blank=True, null=True,
                                   related_name='tags')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('auth.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    class Meta:
        db_table = 'tag'


class Series(models.Model):
    gse_name = models.TextField(blank=True)

    class Meta:
        db_table = 'series'


class SeriesAttribute(models.Model):
    series = models.ForeignKey(Series, blank=True, null=True)
    attribute_value = models.TextField(blank=True)
    attribute_name = models.TextField(blank=True)

    class Meta:
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
    created_by = models.ForeignKey('auth.User', db_column='created_by', blank=True, null=True,
                                   related_name='serie_annotations')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('auth.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    agreed = models.IntegerField(blank=True, null=True)
    fleiss_kappa = models.FloatField(blank=True, null=True)
    obsolete = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        db_table = 'series_tag'


class Sample(models.Model):
    series = models.ForeignKey('Series', blank=True, null=True)
    platform = models.ForeignKey(Platform, blank=True, null=True)
    gsm_name = models.TextField(blank=True)
    deleted = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        db_table = 'sample'


class SampleAttribute(models.Model):
    sample = models.ForeignKey(Sample, blank=True, null=True)
    attribute_value = models.TextField(blank=True)
    attribute_name = models.TextField(blank=True)

    class Meta:
        db_table = 'sample_attribute'


class SampleTag(models.Model):
    sample = models.ForeignKey(Sample, blank=True, null=True)
    series_tag = models.ForeignKey('SeriesTag', blank=True, null=True, related_name='sample_tags')
    annotation = models.TextField(blank=True)
    is_active = models.CharField(max_length=1, blank=True, default='T')
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey('auth.User', db_column='created_by', blank=True, null=True,
                                   related_name='sample_annotations')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('auth.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    objects = DataFrameManager()

    class Meta:
        db_table = 'sample_tag'


class Analysis(models.Model):
    analysis_name = models.CharField(max_length=512)
    description = models.CharField(max_length=512, blank=True, default='')
    case_query = models.CharField(max_length=512)
    control_query = models.CharField(max_length=512)
    modifier_query = models.CharField(max_length=512, blank=True, default='')
    min_samples = models.IntegerField(blank=True, null=True, default=3)
    # Stats
    series_count = models.IntegerField(blank=True, null=True)
    platform_count = models.IntegerField(blank=True, null=True)
    sample_count = models.IntegerField(blank=True, null=True)
    series_ids = models.TextField(blank=True)
    platform_ids = models.TextField(blank=True)
    sample_ids = models.TextField(blank=True)
    # Meta
    is_active = models.CharField(max_length=1, blank=True)
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey('auth.User', db_column='created_by', blank=True, null=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('auth.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')
    deleted = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        db_table = 'analysis'

    def __unicode__(self):
        if self.modifier_query:
            return u'%s: case=%s control=%s modifier=%s' \
                % (self.analysis_name, self.case_query, self.control_query, self.modifier_query)
        else:
            return u'%s: case=%s control=%s' \
                % (self.analysis_name, self.case_query, self.control_query)


class MetaAnalysis(models.Model):
    analysis = models.ForeignKey(Analysis, blank=True, null=True)
    mygene_sym = models.CharField("sym", max_length=512, blank=True)
    mygene_entrez = models.IntegerField("entrez", blank=True, null=True)
    direction = models.CharField(max_length=512, blank=True)
    casedatacount = models.IntegerField('cases', blank=True, null=True)
    controldatacount = models.IntegerField('controls', blank=True, null=True)
    k = models.IntegerField(blank=True, null=True)
    fixed_te = models.FloatField(blank=True, null=True)
    fixed_se = models.FloatField(blank=True, null=True)
    fixed_lower = models.FloatField(blank=True, null=True)
    fixed_upper = models.FloatField(blank=True, null=True)
    fixed_pval = models.FloatField(blank=True, null=True)
    fixed_zscore = models.FloatField(blank=True, null=True)
    random_te = models.FloatField(blank=True, null=True)
    random_se = models.FloatField(blank=True, null=True)
    random_lower = models.FloatField(blank=True, null=True)
    random_upper = models.FloatField(blank=True, null=True)
    random_pval = models.FloatField(blank=True, null=True)
    random_zscore = models.FloatField(blank=True, null=True)
    predict_te = models.FloatField(blank=True, null=True)
    predict_se = models.FloatField(blank=True, null=True)
    predict_lower = models.FloatField(blank=True, null=True)
    predict_upper = models.FloatField(blank=True, null=True)
    predict_pval = models.FloatField(blank=True, null=True)
    predict_zscore = models.FloatField(blank=True, null=True)
    tau2 = models.FloatField(blank=True, null=True)
    tau2_se = models.FloatField(blank=True, null=True)
    c = models.FloatField(blank=True, null=True)
    h = models.FloatField(blank=True, null=True)
    h_lower = models.FloatField(blank=True, null=True)
    h_upper = models.FloatField(blank=True, null=True)
    i2 = models.FloatField(blank=True, null=True)
    i2_lower = models.FloatField(blank=True, null=True)
    i2_upper = models.FloatField(blank=True, null=True)
    q = models.FloatField(blank=True, null=True)
    q_df = models.FloatField(blank=True, null=True)

    objects = DataFrameManager()

    class Meta:
        db_table = 'meta_analysis'
