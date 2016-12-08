from django.db import models
from django.contrib.auth.models import AbstractUser

from legacy.models import Sample, Series, PlatformProbe, Platform, Analysis
from tags.models import (Tag, SeriesTag, SerieValidation,
                         SampleTag, SampleValidation, )


AbstractUser._meta.get_field('username').max_length = 127


class User(AbstractUser):
    is_competent = models.BooleanField(default=False)

    class Meta:
        db_table = 'auth_user'


ATTR_PER_SAMPLE = 32
ATTR_PER_SERIE = 4


class StatisticCacheManager(models.Manager):
    def update_statistics(self):
        from core.tasks import update_graph

        users = list(SeriesTag.objects.values_list('created_by', flat=True))
        users += list(SerieValidation.objects.values_list('created_by', flat=True))

        statistic_schema = {
            'samples': Sample.objects.count(),
            'samples_attributes': Sample.objects.count() * ATTR_PER_SAMPLE,
            'experiments': Series.objects.count(),
            'experiments_attributes': Series.objects.count() * ATTR_PER_SERIE,

            'tags': Tag.objects.count(),
            'serie_annotations': SeriesTag.objects.count() + SerieValidation.objects.count(),
            'sample_annotations': SampleTag.objects.count() + SampleValidation.objects.count(),

            'gene_probes': PlatformProbe.objects.count(),
            'platforms': Platform.objects.count(),
            'meta_analyses': Analysis.objects.count(),

            'users': len(set(users)),
        }

        for slug, value in statistic_schema.iteritems():
            statistic = StatisticCache.objects.get_or_create(
                slug=slug)[0]
            statistic.count = value
            statistic.save()

        update_graph()


class StatisticCache(models.Model):
    slug = models.CharField(max_length=30, unique=True, db_index=True)
    count = models.PositiveIntegerField(default=0)

    objects = StatisticCacheManager()

    def __unicode__(self):
        return self.slug
