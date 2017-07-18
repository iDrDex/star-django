from funcy import (zipdict, isums, walk_values, count_by, group_values,
                   first, join_with, merge, walk_keys, silent)
from collections import defaultdict
from tqdm import tqdm
from handy.db import queryset_iterator
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.db import transaction
from django.core.management import BaseCommand
from core.models import HistoricalCounter
from legacy.models import Series, Sample, Platform
from core.models import User
from tags.models import (Tag, SeriesAnnotation, SeriesTag, SampleTag,
                         SerieValidation, SampleValidation, )

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
SPECIES = {'9606': 'human', '10090': 'mouse', '10116': 'rat'}

def ceil_attrs_date(model):
    month, day, year = model.attrs.get('submission_date', 'Jan 1 1960').split()
    if month == 'Jans':
        month = 'Jan'
    return ceil_date(datetime(int(year), MONTHS.index(month) + 1, 1))

def ceil_date(date):
    next_month = datetime(date.year, date.month, 1) + timedelta(days=31)
    return datetime(next_month.year, next_month.month, 1)


START_DATE = datetime(2014, 10, 1)
CURRENT_DATE = ceil_date(datetime.now())

def accumulate(data):
    dates, counts = zip(*sorted(data.items()))
    return zipdict(dates, isums(counts))

def get_value(keys, index):
    def _getter(item):
        if index < 0:
            return 0
        return item.get(
            keys[index],
            get_value(keys, index - 1)(item))
    return _getter


def distribute_by_user_id(qs):
    data = group_values(qs.values_list('created_by_id', 'created_on'))
    return walk_values(lambda dates: accumulate(count_by(ceil_date, dates)), data)


def distribute_by_created_on(qs):
    return accumulate(count_by(ceil_date, qs.values_list('created_on', flat=True)))


def distribute_series_and_sample_annotations(qs):
    series_annotations = distribute_by_created_on(qs)
    values = qs.values_list('created_on', 'samples')
    group = group_values(walk_keys(ceil_date, values.iterator()))
    return series_annotations, accumulate(walk_values(sum, group))


def get_series_tag_history():
    series_tag_history = {
        'created': defaultdict(int),
        'validated': defaultdict(int),
        'invalidated': defaultdict(int)
    }
    qs = SeriesTag.objects.filter(is_active=True).prefetch_related('validations')

    for tag in tqdm(qs, total=qs.count(), desc='series tag history'):
        validations = list(tag.validations.all())
        series_tag_history['created'][ceil_date(tag.created_on)] += 1
        validated = silent(min)(
            v.created_on
            for v in validations
            if v.annotation_kappa == 1)
        if validated:
            series_tag_history['validated'][ceil_date(validated)] += 1
            invalidated = silent(min)(
                v.created_on
                for v in validations
                if v.agrees_with is not None)
            if invalidated:
                series_tag_history['invalidated'][ceil_date(invalidated)] += 1

    return walk_values(accumulate, series_tag_history)


class Command(BaseCommand):
    def handle(self, *args, **options):
        series = {}
        samples = {}

        platform_created_on = join_with(
            min,
            [{p: ceil_attrs_date(s) for p in s.platforms}
             for s in Series.objects.all()])
        platform_qs = Platform.objects.annotate(probes_count=Count('probes'))\
            .values('gpl_name', 'probes_count')
        platforms = {}
        platforms_probes = {}

        series_annotations = {}
        sample_annotations = {}
        concordant_series_annotations = {}
        concordant_sample_annotations = {}

        series_tags = {}
        concordant_series_tags = {}
        sample_tags = {}
        concordant_sample_tags = {}

        series_validations = {}
        sample_validations = {}
        concordant_series_validations = {}
        concordant_sample_validations = {}

        for specie in SPECIES.values():
            series[specie] = accumulate(count_by(
                ceil_attrs_date, Series.objects.filter(specie=specie)))

            qs = Sample.objects.filter(platform__specie=specie)
            iterator = tqdm(queryset_iterator(qs, 30000),
                            total=qs.count(),
                            desc='{0} samples'.format(specie))
            samples[specie] = accumulate(count_by(ceil_attrs_date, iterator))

            platforms_data = [
                [platform_created_on[item['gpl_name']], item['probes_count']]
                for item in platform_qs.filter(specie=specie)
            ]
            platforms[specie] = accumulate(count_by(first, platforms_data))
            group = group_values(platforms_data)
            platforms_probes[specie] = accumulate(walk_values(sum, group))

            qs = SeriesAnnotation.objects.filter(series__specie=specie)
            series_annotations[specie], \
                sample_annotations[specie] = distribute_series_and_sample_annotations(qs)

            concordant_series_annotations[specie], \
                concordant_sample_annotations[specie] = distribute_series_and_sample_annotations(
                    qs.filter(best_cohens_kappa=1))

            qs = SeriesTag.objects.filter(platform__specie=specie, is_active=True)
            series_tags[specie] = distribute_by_created_on(qs)
            concordant_series_tags[specie] = distribute_by_created_on(
                qs.exclude(agreed=None))

            qs = SampleTag.objects.filter(sample__platform__specie=specie, is_active=True)
            sample_tags[specie] = distribute_by_created_on(qs)
            concordant_sample_tags[specie] = distribute_by_created_on(
                qs.exclude(series_tag__agreed=None))

            qs = SerieValidation.objects.filter(platform__specie=specie,
                                                ignored=False, by_incompetent=False)
            series_validations[specie] = distribute_by_created_on(qs)
            concordant_series_validations[specie] = distribute_by_created_on(
                qs.filter(best_kappa=1))

            qs = SampleValidation\
                .objects\
                .filter(sample__platform__specie=specie,
                        serie_validation__ignored=False,
                        serie_validation__by_incompetent=False)
            sample_validations[specie] = distribute_by_created_on(qs)
            concordant_sample_validations[specie] = distribute_by_created_on(
                qs.filter(Q(serie_validation__best_kappa=1) | Q(concordant=True)))

        users = accumulate(count_by(ceil_date, User.objects.values_list('date_joined', flat=True)))
        tags = accumulate(count_by(ceil_date, Tag.objects.values_list('created_on', flat=True)))

        delta = CURRENT_DATE - START_DATE
        keys = sorted(set(ceil_date(START_DATE + timedelta(days=index * 20))
                          for index in range(delta.days / 20 + 1)))

        specie_data = {
            'series': series,
            'samples': samples,
            'platforms': platforms,
            'platforms_probes': platforms_probes,
            'series_annotations': series_annotations,
            'sample_annotations': sample_annotations,
            'concordant_series_annotations': concordant_series_annotations,
            'concordant_sample_annotations': concordant_sample_annotations,
            'series_tags': series_tags,
            'sample_tags': sample_tags,
            'concordant_series_tags': concordant_series_tags,
            'concordant_sample_tags': concordant_sample_tags,
            'series_validations': series_validations,
            'sample_validations': sample_validations,
            'concordant_series_validations': concordant_series_validations,
            'concordant_sample_validations': concordant_sample_validations,
            'series_tags_by_users': distribute_by_user_id(SeriesTag.objects.filter(is_active=True)),
            'sample_tags_by_users': distribute_by_user_id(SampleTag.objects.filter(is_active=True)),
            'series_validations_by_users': distribute_by_user_id(
                SerieValidation.objects.filter(ignored=False, by_incompetent=False)),
            'sample_validations_by_users': distribute_by_user_id(
                SampleValidation.objects.filter(
                    serie_validation__ignored=False,
                    serie_validation__by_incompetent=False)),
            'series_tag_history': get_series_tag_history(),
        }

        data = {
            'users': users,
            'tags': tags,
        }

        with transaction.atomic():
            HistoricalCounter.objects.filter(created_on__lte=CURRENT_DATE).delete()
            HistoricalCounter.objects.bulk_create([
                HistoricalCounter(
                    created_on=key,
                    counters=merge(
                        walk_values(get_value(keys, index), data),
                        walk_values(lambda value:
                                    walk_values(get_value(keys, index), value),
                                    specie_data)))
                for index, key in enumerate(keys)])
