from decimal import Decimal
from django.db import models
from handy.models import JSONField


SAMPLE_REWARD = Decimal('0.05')


class UserStats(models.Model):
    user = models.OneToOneField('legacy.AuthUser', primary_key=True, related_name='stats')

    serie_tags = models.IntegerField(default=0)
    sample_tags = models.IntegerField(default=0)
    serie_validations = models.IntegerField(default=0)
    sample_validations = models.IntegerField(default=0)
    serie_validations_concordant = models.IntegerField(default=0)
    sample_validations_concordant = models.IntegerField(default=0)

    samples_to_pay_for = models.IntegerField(default=0)
    samples_payed = models.IntegerField(default=0)

    @property
    def serie_validation_concordancy(self):
        if self.serie_validations:
            return float(self.serie_validations_concordant) / self.serie_validations
        else:
            return None

    @property
    def samples_unpayed(self):
        return self.samples_to_pay_for - self.samples_payed

    @property
    def amount_unpayed(self):
        return self.samples_unpayed * SAMPLE_REWARD


class PaymentState(object):
    PENDING, DONE, FAILED = 1, 2, 3
    choices = (
        (1, 'pending'),
        (2, 'done'),
        (3, 'failed'),
    )


class Payment(models.Model):
    receiver = models.ForeignKey('legacy.AuthUser', related_name='payments')
    samples = models.IntegerField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('legacy.AuthUser')
    state = models.IntegerField(choices=PaymentState.choices)
    extra = JSONField(default={})

    @property
    def failed(self):
        return self.state == PaymentState.FAILED


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

    @property
    def concordant(self):
        return self.samples_concordant == self.samples_total


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
