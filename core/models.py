from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from legacy.models import Sample, Series, Platform, Analysis
from tags.models import Tag, RawSeriesAnnotation, RawSampleAnnotation
from handy.models import JSONField


AbstractUser._meta.get_field('username').max_length = 127


class User(AbstractUser):
    is_competent = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_user'

@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


ATTR_PER_SAMPLE = 32
ATTR_PER_SERIE = 4


class StatisticCacheManager(models.Manager):
    def update_statistics(self):
        from core.tasks import update_graph
        update_graph()

        users = RawSeriesAnnotation.objects.values_list('created_by', flat=True).distinct().count()
        samples = Sample.objects.exclude(deleted='T').count()
        series = Series.objects.count()

        statistic_schema = {
            'samples': samples,
            'samples_attributes': samples * ATTR_PER_SAMPLE,
            'experiments': series,
            'experiments_attributes': series * ATTR_PER_SERIE,

            'tags': Tag.objects.count(),
            'series_annotations': RawSeriesAnnotation.objects.count(),
            'sample_annotations': RawSampleAnnotation.objects.count(),

            'gene_probes': Platform.objects.aggregate(s=Sum('probes_matched'))['s'],
            'platforms': Platform.objects.count(),
            'meta_analyses': Analysis.objects.count(),

            'users': users,
        }

        for slug, value in statistic_schema.items():
            statistic = StatisticCache.objects.get_or_create(
                slug=slug)[0]
            statistic.count = value
            statistic.save()


class StatisticCache(models.Model):
    slug = models.CharField(max_length=30, unique=True, db_index=True)
    count = models.PositiveIntegerField(default=0)

    objects = StatisticCacheManager()

    def __str__(self):
        return self.slug


class HistoricalCounter(models.Model):
    created_on = models.DateTimeField()
    counters = JSONField()

    def __str__(self):
        return 'Counters for {0}'.format(self.created_on)
