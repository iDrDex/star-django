from decimal import Decimal
from django.db import models
from django.db.models import Count
from handy.models import JSONField
from django_pandas.managers import DataFrameManager


ANNOTATION_REWARD = Decimal('0.05')
VALIDATION_REWARD = Decimal('0.03')


class Tag(models.Model):
    tag_name = models.CharField(max_length=512)
    description = models.CharField(max_length=512, blank=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey('core.User', db_column='created_by', blank=True, null=True,
                                   related_name='tags')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('core.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    class Meta:
        db_table = 'tag'

    def get_stats(self):
        from tags.models import SampleValidation, SampleAnnotation

        def annotate(qs):
            return list(qs.values_list('annotation').annotate(Count('id')).order_by('annotation'))

        return {
            'annotations': annotate(SampleTag.objects.filter(series_tag__tag=self)),
            'validations': annotate(SampleValidation.objects.filter(serie_validation__tag=self)),
            'canonical': annotate(SampleAnnotation.objects.filter(serie_annotation__tag=self)),
        }

    def remap_annotations(self, old, new):
        """
        When boolean tag changes its name we need to update all annotations.
        """
        from tags.models import SampleValidation, SampleAnnotation

        if old != new:
            SampleTag.objects.filter(series_tag__tag=self, annotation=old).update(annotation=new)
            SampleValidation.objects.filter(serie_validation__tag=self, annotation=old) \
                            .update(annotation=new)
            SampleAnnotation.objects.filter(serie_annotation__tag=self, annotation=old) \
                            .update(annotation=new)

    def remap_refs(self, new_pk):
        """
        Remap any references to this tag to other one. Used in tag merge.
        """
        from tags.models import SerieValidation, SerieAnnotation

        SeriesTag.objects.filter(tag=self).update(tag=new_pk)
        SerieValidation.objects.filter(tag=self).update(tag=new_pk)
        SerieAnnotation.objects.filter(tag=self).update(tag=new_pk)


class SeriesTag(models.Model):
    series = models.ForeignKey('legacy.Series', blank=True, null=True)
    platform = models.ForeignKey('legacy.Platform', blank=True, null=True)
    tag = models.ForeignKey(Tag, blank=True, null=True)
    header = models.CharField(max_length=512, blank=True)
    regex = models.CharField(max_length=512, blank=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey('core.User', db_column='created_by', blank=True, null=True,
                                   related_name='serie_annotations')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('core.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    agreed = models.IntegerField(blank=True, null=True)
    fleiss_kappa = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'series_tag'


class SampleTag(models.Model):
    sample = models.ForeignKey('legacy.Sample', blank=True, null=True)
    series_tag = models.ForeignKey(SeriesTag, blank=True, null=True, related_name='sample_tags')
    annotation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    created_by = models.ForeignKey('core.User', db_column='created_by', blank=True, null=True,
                                   related_name='sample_annotations')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    modified_by = models.ForeignKey('core.User', db_column='modified_by', blank=True, null=True,
                                    related_name='+')

    objects = DataFrameManager()

    class Meta:
        db_table = 'sample_tag'

###

class UserStats(models.Model):
    user = models.OneToOneField('core.User', primary_key=True, related_name='stats')

    serie_tags = models.IntegerField(default=0)
    sample_tags = models.IntegerField(default=0)
    serie_validations = models.IntegerField(default=0)
    sample_validations = models.IntegerField(default=0)
    serie_validations_concordant = models.IntegerField(default=0)
    sample_validations_concordant = models.IntegerField(default=0)

    # Purely stats
    earned_sample_annotations = models.IntegerField(default=0)
    earned_sample_validations = models.IntegerField(default=0)

    # Used for payments
    earned = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payed = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    @property
    def serie_validation_concordancy(self):
        if self.serie_validations:
            return float(self.serie_validations_concordant) / self.serie_validations
        else:
            return None

    @property
    def unpayed(self):
        return self.earned - self.payed

    def earn_annotations(self, count):
        self.earned_sample_annotations += count
        self.earned += ANNOTATION_REWARD * count

    def earn_validations(self, count):
        self.earned_sample_validations += count
        self.earned += VALIDATION_REWARD * count


class PaymentState(object):
    PENDING, DONE, FAILED = 1, 2, 3
    choices = (
        (1, 'pending'),
        (2, 'done'),
        (3, 'failed'),
    )


class Payment(models.Model):
    receiver = models.ForeignKey('core.User', related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User')
    state = models.IntegerField(choices=PaymentState.choices)
    extra = JSONField(default={})

    @property
    def failed(self):
        return self.state == PaymentState.FAILED


class ValidationJob(models.Model):
    series_tag = models.ForeignKey(SeriesTag, on_delete=models.CASCADE)
    locked_on = models.DateTimeField(blank=True, null=True)
    locked_by = models.ForeignKey('core.User', blank=True, null=True)
    # generation = models.IntegerField(default=1)
    priority = models.FloatField(default=0)

    class Meta:
        db_table = 'validation_job'


class SerieValidation(models.Model):
    series_tag = models.ForeignKey(SeriesTag, related_name='validations',
                                   blank=True, null=True, on_delete=models.SET_NULL)
    series = models.ForeignKey('legacy.Series', related_name='validations')
    platform = models.ForeignKey('legacy.Platform', related_name='validations')
    tag = models.ForeignKey(Tag, related_name='validations')
    column = models.CharField(max_length=512, blank=True)
    regex = models.CharField(max_length=512, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.User')
    on_demand = models.BooleanField(default=False)
    ignored = models.BooleanField(default=False)

    # Calculated fields
    samples_total = models.IntegerField(null=True)
    samples_concordant = models.IntegerField(null=True)
    annotation_kappa = models.FloatField(blank=True, null=True)
    best_kappa = models.FloatField(blank=True, null=True)

    agrees_with = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

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
    created_by = models.ForeignKey('core.User')

    # Calculated field
    concordant = models.NullBooleanField(null=True)

    class Meta:
        db_table = 'sample_validation'


class SerieAnnotation(models.Model):
    """
    This model is to store best available annotations.
    You can also restrict quality by filtering on fleiss_kappa or best_cohens_kappa.
    """
    series_tag = models.OneToOneField(SeriesTag, related_name='canonical')
    series = models.ForeignKey('legacy.Series', blank=True, null=True)
    platform = models.ForeignKey('legacy.Platform', blank=True, null=True)
    tag = models.ForeignKey(Tag, blank=True, null=True)
    header = models.CharField(max_length=512, blank=True)
    regex = models.CharField(max_length=512, blank=True)
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)

    annotations = models.IntegerField()
    authors = models.IntegerField()
    fleiss_kappa = models.FloatField(blank=True, null=True)
    best_cohens_kappa = models.FloatField(blank=True, null=True)
    samples = models.IntegerField(default=0)

    class Meta:
        db_table = 'series_annotation'

    @classmethod
    def create_from_series_tag(cls, st):
        return cls.objects.create(
            series_tag_id=st.id,
            series_id=st.series_id, platform_id=st.platform_id, tag_id=st.tag_id,
            header=st.header, regex=st.regex or '',
            annotations=1, authors=1
        )

    def fill_samples(self, sample_annos):
        self.samples = len(sample_annos)
        self.save()
        SampleAnnotation.objects.bulk_create([
            SampleAnnotation(serie_annotation=self,
                             sample_id=obj.sample_id, annotation=obj.annotation or '')
            for obj in sample_annos
        ])


class SampleAnnotation(models.Model):
    serie_annotation = models.ForeignKey(SerieAnnotation, related_name='sample_annotations')
    sample = models.ForeignKey('legacy.Sample')
    annotation = models.TextField(blank=True)

    objects = DataFrameManager()

    class Meta:
        db_table = 'sample_annotation'
