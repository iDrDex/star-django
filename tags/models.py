from django.db import models


class ValidationJob(models.Model):
    series_tag = models.ForeignKey('legacy.SeriesTag', on_delete=models.CASCADE)
    locked_on = models.DateTimeField(blank=True, null=True)
    locked_by = models.ForeignKey('legacy.AuthUser', blank=True, null=True)

    class Meta:
        db_table = 'validation_job'


class SerieValidation(models.Model):
    series_tag = models.ForeignKey('legacy.SeriesTag', related_name='validations',
                                   blank=True, null=True, on_delete=models.SET_NULL)
    series = models.ForeignKey('legacy.Series', related_name='validations')
    platform = models.ForeignKey('legacy.Platform', related_name='validations')
    tag = models.ForeignKey('legacy.Tag', related_name='validations')
    column = models.CharField(max_length=512, blank=True)
    regex = models.CharField(max_length=512, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('legacy.AuthUser')

    # Calculated fields
    samples_total = models.IntegerField(null=True)
    samples_concordant = models.IntegerField(null=True)
    samples_concordancy = models.FloatField(null=True)

    class Meta:
        db_table = 'series_validation'


class SampleValidation(models.Model):
    sample = models.ForeignKey('legacy.Sample', blank=True, null=True)
    serie_validation = models.ForeignKey(SerieValidation, related_name='sample_validations')
    annotation = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('legacy.AuthUser')

    # Calculated field
    concordant = models.NullBooleanField(null=True)

    class Meta:
        db_table = 'sample_validation'


class LegacyRouter(object):
    def db_for_write(self, model, **hints):
        if is_legacy(model):
            return 'legacy'
    db_for_read = db_for_write

    def allow_relation(self, obj1, obj2, **hints):
        return is_legacy(obj1.__class__) == is_legacy(obj2.__class__)

    def allow_migrate(self, db, model):
        return is_legacy(model) == (db == 'legacy')


def is_legacy(model):
    return model._meta.app_label in {'legacy', 'tags'}
