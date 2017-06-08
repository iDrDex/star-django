from funcy import zipdict, isums, walk_values, group_by, count_by, second, compose, first
from tqdm import tqdm
from handy.db import queryset_iterator
from datetime import datetime
from django.db.models import Count
from django.db import transaction
from django.core.management import BaseCommand
from core.models import HistoricalCounter
from legacy.models import Series, Sample, Platform, PlatformProbe
from core.models import User
from tags.models import Tag, SerieAnnotation, SampleAnnotation

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def floor_attrs_date(model):
    month, day, year = model.attrs.get('submission_date', 'Jan 1 1960').split()
    if month == 'Jans':
        month = 'Jan'
    return datetime(int(year), MONTHS.index(month) + 1, 1)

def floor_date(date):
    return datetime(date.year, date.month, 1)


START_DATE = datetime(2014, 1, 1)
CURRENT_DATE = floor_date(datetime.now())

def accumulate(data):
    dates, counts = zip(*sorted(data.items()))
    return zipdict(dates, isums(counts))

def gather_by(fn, iterator, date_floor):
    def _gather_fn(array):
        return sum(map(fn, array))
    return walk_values(_gather_fn, group_by(date_floor, iterator))

class Command(BaseCommand):
    def handle(self, *args, **options):
        # TODO
        # * Fix holes

        series = accumulate(count_by(floor_attrs_date, Series.objects.all()))

        iterator = tqdm(queryset_iterator(Sample.objects.all(), 30000),
                        total=Sample.objects.count(),
                        desc='samples')
        samples = accumulate(count_by(floor_attrs_date, iterator))

        iterator = tqdm(Platform.objects.all().annotate(probes_count=Count('probes')).iterator(),
                        total=Platform.objects.count(),
                        desc='platforms')
        platforms_data = [
            {
                'created_on': min(map(floor_attrs_date, platform.sample_set.all())),
                'probes_count': platform.probes_count
            }
            for platform in iterator
        ]
        platforms = accumulate(count_by(lambda p: p['created_on'], platforms_data))
        platforms_probes = accumulate(gather_by(
            lambda p: p['probes_count'],
            platforms_data,
            lambda p: p['created_on']))

        users = accumulate(count_by(floor_date, User.objects.values_list('date_joined', flat=True)))

        tags = accumulate(count_by(floor_date, Tag.objects.values_list('created_on', flat=True)))

        qs = SerieAnnotation.objects.values_list('created_on', flat=True)
        serie_annotations = accumulate(count_by(floor_date, qs))

        qs = SerieAnnotation.objects.all()\
            .annotate(samples_annotation_count=Count('sample_annotations'))\
            .values_list('created_on', 'samples_annotation_count')

        sample_annotations = accumulate(gather_by(second, qs, compose(floor_date, first)))

        keys = sorted(
            [key for key in set(series.keys() +
                                samples.keys() +
                                platforms.keys() +
                                platforms_probes.keys() +
                                users.keys() +
                                tags.keys() +
                                sample_annotations.keys())
             if key >= START_DATE and key < CURRENT_DATE])

        data = {
            'series': series,
            'samples': samples,
            'platforms': platforms,
            'platforms_probes': platforms_probes,
            'users': users,
            'tags': tags,
            'serie_annotations': serie_annotations,
            'sample_annotations': sample_annotations,
        }

        with transaction.atomic():
            HistoricalCounter.objects.filter(created_on__lte=CURRENT_DATE).delete()
            HistoricalCounter.objects.bulk_create([
                HistoricalCounter(
                    created_on=key,
                    counters=walk_values(lambda item: item.get(key, 0), data))
                for key in keys])
            HistoricalCounter.objects.create(
                created_on=CURRENT_DATE,
                counters={
                    'series': Series.objects.count(),
                    'samples': Sample.objects.count(),
                    'platforms': Platform.objects.count(),
                    'platforms_probes': PlatformProbe.objects.count(),
                    'users': User.objects.count(),
                    'tags': Tag.objects.count(),
                    'serie_annotations': SerieAnnotation.objects.count(),
                    'sample_annotations': SampleAnnotation.objects.count(),
                })
