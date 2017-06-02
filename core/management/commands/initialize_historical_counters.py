from funcy import *
from collections import defaultdict
from datetime import datetime
from django.db.models import Count
from django.core.management import BaseCommand
from core.models import HistoricalCounter
from legacy.models import Series, Sample
from core.models import User
from tags.models import Tag, SerieAnnotation

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def attrs_date_ceiling(serie):
    month, day, year = serie.attrs.get('submission_date', 'Jan 1 1960').split()
    if month == 'Jans':
        month = 'Jan'
    return datetime(int(year), MONTHS.index(month) + 1, 1)

def model_date_ceiling(field):
    def _date_celling(instance):
        date = getattr(instance, field)
        return datetime(date.year, date.month, 1)
    return _date_celling

def count_sample_annotations(serie_annotation):
    return serie_annotation.sample_annotations.count()

def cumulate(data):
    dates, counts = zip(*sorted(data.items()))
    return zipdict(dates, isums(counts))

def gather(qs, date_ceiling):
    return count_by(date_ceiling, qs)

def gather_by(fn, qs, date_ceiling):
    def _gather_fn(array):
        return sum(map(fn, array))
    return walk_values(_gather_fn, group_by(date_ceiling, qs))

def chunked_gather(qs, date_celling):
    chunk_size = 30000
    total = qs.count()
    offset = 0
    limit = chunk_size

    print("Total {}".format(total / chunk_size))
    index = 0

    result = defaultdict(int)

    while limit < total:
        index += 1
        print("Current {}".format(index))
        result = merge_with(sum, result, gather(qs[offset:limit], date_celling))
        offset = limit
        limit = limit + chunk_size

    return merge_with(sum, result, gather(qs[offset:total], date_celling))


class Command(BaseCommand):
    def handle(self, *args, **options):
        # TODO
        # * Fix holes
        # * Calculate platforms and probes

        series = cumulate(gather(Series.objects.all(), attrs_date_ceiling))
        samples = cumulate(chunked_gather(Sample.objects.all(), attrs_date_ceiling))
        # platforms = ???
        # platforms_probes = ???
        users = cumulate(gather(User.objects.all(), model_date_ceiling('date_joined')))
        tags = cumulate(gather(Tag.objects.all(), model_date_ceiling('created_on')))
        serie_annotations = cumulate(gather(SerieAnnotation.objects.all(),
                                            model_date_ceiling('created_on')))
        sample_annotations = cumulate(gather_by(
            lambda i: getattr(i, 'samples_annotation_count'),
            SerieAnnotation.objects.all().annotate(
                samples_annotation_count=Count('sample_annotations')),
            model_date_ceiling('created_on')))

        keys = [key for key in set(series.keys() +
                                   samples.keys() +
                                   users.keys() +
                                   tags.keys() +
                                   sample_annotations.keys())
                if key >= datetime(2014, 1, 1)]

        HistoricalCounter.objects.filter(timestamp__lte=datetime(2017, 6, 1)).delete()
        for key in sorted(keys):
            data = {
                'series': series.get(key, 0),
                'samples': samples.get(key, 0),
                'users': users.get(key, 0),
                'tags': tags.get(key, 0),
                'serie_annotations': serie_annotations.get(key, 0),
                'sample_annotations': sample_annotations.get(key, 0),
            }
            HistoricalCounter.objects.create(timestamp=key, data=data)
