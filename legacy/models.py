from __future__ import unicode_literals

from django.db import models
from django_pandas.managers import DataFrameManager


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


class Sample(models.Model):
    series = models.ForeignKey('Series', blank=True, null=True)
    platform = models.ForeignKey(Platform, blank=True, null=True)
    gsm_name = models.TextField(blank=True)
    # TODO: refactor deleted -> is_active, get rid of char boolean
    # NOTE: leaving it as is for now to not mess with sample_view
    # is_active = models.BooleanField(default=True)
    deleted = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        db_table = 'sample'


class SampleAttribute(models.Model):
    sample = models.ForeignKey(Sample, blank=True, null=True)
    attribute_value = models.TextField(blank=True)
    attribute_name = models.TextField(blank=True)

    class Meta:
        db_table = 'sample_attribute'


# class SeriesMatrix(models.Model):
#     gse_name = models.CharField(max_length=127)
#     gpl_name = models.CharField(max_length=127)
#     last_updated = models.DateField()
#     matrix = S3Field()

#     class Meta:
#         unique_together = ('gse_name', 'gpl_name', 'last_updated')


from s3field import S3Field

def analysis_s3name(self):
    return '%s-%s' % (self.pk, self.analysis_name)

class Analysis(models.Model):
    analysis_name = models.CharField(max_length=512)
    description = models.CharField(max_length=512, blank=True, default='')
    case_query = models.CharField(max_length=512)
    control_query = models.CharField(max_length=512)
    modifier_query = models.CharField(max_length=512, blank=True, default='')
    min_samples = models.IntegerField(blank=True, null=True, default=3)
    # Reproducibility
    df = S3Field(null=True, make_name=analysis_s3name)
    fold_changes = S3Field(null=True, make_name=analysis_s3name, compress=True)
    # series_matrices = S3ArrayField(bucket='series_matrices')
    # Stats
    series_count = models.IntegerField(blank=True, null=True)
    platform_count = models.IntegerField(blank=True, null=True)
    sample_count = models.IntegerField(blank=True, null=True)
    series_ids = models.TextField(blank=True)
    platform_ids = models.TextField(blank=True)
    sample_ids = models.TextField(blank=True)
    # Meta
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey('core.User', db_column='created_by', blank=True, null=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('core.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')
    success = models.BooleanField(default=False)

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
    k = models.IntegerField(blank=True, null=True)
    casedatacount = models.IntegerField('cases', blank=True, null=True)
    controldatacount = models.IntegerField('controls', blank=True, null=True)
    random_pval = models.FloatField(blank=True, null=True)
    random_te = models.FloatField(blank=True, null=True)
    random_se = models.FloatField(blank=True, null=True)
    random_lower = models.FloatField(blank=True, null=True)
    random_upper = models.FloatField(blank=True, null=True)
    random_zscore = models.FloatField(blank=True, null=True)
    fixed_pval = models.FloatField(blank=True, null=True)
    fixed_te = models.FloatField(blank=True, null=True)
    fixed_se = models.FloatField(blank=True, null=True)
    fixed_lower = models.FloatField(blank=True, null=True)
    fixed_upper = models.FloatField(blank=True, null=True)
    fixed_zscore = models.FloatField(blank=True, null=True)
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
