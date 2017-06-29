import re
from collections import OrderedDict
from decimal import Decimal
import json
from funcy import icat, walk_keys

from django.db import models
from django.db.models import Count
from django.utils import timezone

from handy.models import JSONField
from django_pandas.managers import DataFrameManager
from s3field import S3MultiField


ANNOTATION_REWARD = Decimal('0.05')
VALIDATION_REWARD = Decimal('0.03')


class Tag(models.Model):
    tag_name = models.CharField(max_length=512)
    description = models.CharField(max_length=512, blank=True)

    ontology_id = models.CharField(max_length=127, blank=True)
    concept_full_id = models.CharField(max_length=512, blank=True)
    concept_name = models.CharField(max_length=512, blank=True)

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

    # Number of validation, which led to first agreement
    # (with whatever previous one, not necessarily initial)
    agreed = models.IntegerField(blank=True, null=True)
    fleiss_kappa = models.FloatField(blank=True, null=True)
    note = models.TextField(blank=True, default='')
    from_api = models.BooleanField(default=False)

    class Meta:
        db_table = 'series_tag'


class SampleTag(models.Model):
    sample = models.ForeignKey('legacy.Sample', blank=True, null=True)
    series_tag = models.ForeignKey(SeriesTag, blank=True, null=True, related_name='sample_tags')
    annotation = models.TextField(blank=True, default='')
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
    by_incompetent = models.BooleanField(default=False)
    note = models.TextField(blank=True, default='')
    from_api = models.BooleanField(default=False)

    # Calculated fields
    samples_total = models.IntegerField(null=True)
    samples_concordant = models.IntegerField(null=True)
    annotation_kappa = models.FloatField(blank=True, null=True)
    best_kappa = models.FloatField(blank=True, null=True)
    agrees_with = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'series_validation'

    # TODO: get rid of samples_concordant and concordant field in sample validations
    @property
    def concordant(self):
        return self.samples_concordant == self.samples_total

    @property
    def same_as_canonical(self):
        samples = dict(self.sample_validations.values_list('sample_id', 'annotation'))
        canonical_samples = dict(self.series_tag.canonical.sample_annotations
                                     .values_list('sample_id', 'annotation'))
        return samples == canonical_samples


class SampleValidation(models.Model):
    sample = models.ForeignKey('legacy.Sample', blank=True, null=True)
    serie_validation = models.ForeignKey(SerieValidation, related_name='sample_validations')
    annotation = models.TextField(blank=True, default='')
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
    series = models.ForeignKey('legacy.Series')
    platform = models.ForeignKey('legacy.Platform')
    tag = models.ForeignKey(Tag)
    header = models.CharField(max_length=512, blank=True)
    regex = models.CharField(max_length=512, blank=True)
    created_on = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)

    annotations = models.IntegerField()
    authors = models.IntegerField()
    fleiss_kappa = models.FloatField(blank=True, null=True)
    best_cohens_kappa = models.FloatField(blank=True, null=True)
    samples = models.IntegerField(default=0)
    captive = models.BooleanField(default=False)

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

    def save(self, **kwargs):
        self.captive = re.compile(self.regex or '').groups > 0
        super(SerieAnnotation, self).save(**kwargs)


class SampleAnnotation(models.Model):
    serie_annotation = models.ForeignKey(SerieAnnotation, related_name='sample_annotations')
    sample = models.ForeignKey('legacy.Sample')
    annotation = models.TextField(blank=True, default='')

    objects = DataFrameManager()

    class Meta:
        db_table = 'sample_annotation'


class Snapshot(models.Model):
    author = models.ForeignKey('core.User')
    title = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    metadata = JSONField(default={})
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    frozen = models.BooleanField(default=False)
    frozen_on = models.DateTimeField(blank=True, null=True)
    files = S3MultiField(compress='gzip')

    class Meta:
        db_table = 'snapshot'

    @property
    def empty(self):
        return not self.metadata.get('searches')

    def add(self, search, qs):
        if self.frozen:
            raise ValueError("Can't add anything to frozen snapshot")
        if not search:
            raise ValueError("Should not add all annotations to snapshot")

        if search in self.metadata.get('searches', {}):
            return False, "This search is already in"
        ids = list(qs.values_list('id', flat=True))
        if set(ids) <= set(self.metadata.get('ids', [])):
            return False, "All matched annotations are already in"

        self.metadata.setdefault('searches', {})
        self.metadata['searches'][search] = {'count': qs.count(), 'ids': ids}
        self.metadata.setdefault('ids', [])
        self.metadata['ids'].extend(i for i in ids if i not in self.metadata['ids'])
        return True, ""

    def remove(self, search):
        if search not in self.metadata.get('searches', {}):
            return False, "This search is not in"

        self.metadata['searches'].pop(search)
        self.metadata['ids'] = list(set(icat(s['ids'] for s in self.metadata['searches'].values())))
        return True, ""

    def freeze(self):
        filename = '%s-%s' % (self.pk, self.title) if self.title else str(self.pk)
        data = self._get_data()
        # JSON
        json_data = json.dumps(data, ensure_ascii=True, separators=(',', ':'))
        self.upload_files({'data': json_data, 'name': filename + '.json.gz', 'format': 'json'},
                          lazy=True)
        # CSV
        csv_data = csv_dumps(data)
        self.upload_files({'data': csv_data, 'name': filename + '.csv.gz', 'format': 'csv'},
                          lazy=True)

        # Freeze
        self.frozen = True
        self.frozen_on = timezone.now()
        self.save()

    # Prepare data
    KEYS = OrderedDict([
        ('sample_id', 'sample_id'),
        ('sample__gsm_name', 'gsm_name'),
        ('annotation', 'annotation'),
        ('serie_annotation_id', 'serie_annotation_id'),
        ('serie_annotation__series_id', 'serie_id'),
        ('serie_annotation__series__gse_name', 'gse_name'),
        ('sample__platform_id', 'platform_id'),
        ('sample__platform__gpl_name', 'gpl_name'),
        ('serie_annotation__tag_id', 'tag_id'),
        ('serie_annotation__tag__tag_name', 'tag_name'),
        ('serie_annotation__tag__concept_full_id', 'tag_concept_full_id'),
    ])

    def _get_data(self):
        qs = SampleAnnotation.objects.values(*self.KEYS).prefetch_related(
            'sample',
            'sample__platform',
            'serie_annotation__tag',
        ).filter(serie_annotation_id__in=self.metadata.get('ids', []))
        return [walk_keys(self.KEYS, annotation) for annotation in qs.iterator()]


import csv
from cStringIO import StringIO
from contextlib import closing

def csv_dumps(data):
    if not data:
        return ''
    with closing(StringIO()) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())

        writer.writeheader()
        for row in data:
            writer.writerow(row)
        return csvfile.getvalue()
