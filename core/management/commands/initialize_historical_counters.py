from funcy import *
from tqdm import tqdm
from handy.db import queryset_iterator
from datetime import datetime, timedelta
from django.db.models import Count, Q
from django.db import transaction
from django.core.management import BaseCommand
from core.models import HistoricalCounter
from legacy.models import Series, Sample, Platform
from core.models import User
from tags.models import Tag, SerieAnnotation, SeriesTag, SampleTag, SerieValidation, SampleValidation

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
SPECIES = {'9606': 'human', '10090': 'mouse', '10116': 'rat'}
# SPECIES = {'10116': 'rat'}

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

        serie_annotations = {}
        sample_annotations = {}
        concordant_serie_annotations = {}
        concordant_sample_annotations = {}

        series_tags = {}
        concordant_series_tags = {}
        sample_tags = {}
        concordant_sample_tags = {}

        serie_validations = {}
        sample_validations = {}
        concordant_serie_validations = {}
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

            qs = SerieAnnotation.objects.filter(series__specie=specie)

            def setup_annotation_data_by_qs(qs, current_serie_annotations, current_sample_annotations):
                current_serie_annotations[specie] = accumulate(count_by(
                    ceil_date, qs.values_list('created_on', flat=True)))
                values = qs.annotate(samples_annotation_count=Count('sample_annotations'))\
                    .values_list('created_on', 'samples_annotation_count')
                group = group_values((ceil_date(date), count) for (date, count) in values.iterator())
                current_sample_annotations[specie] = accumulate(walk_values(sum, group))

            setup_annotation_data_by_qs(qs,
                                        serie_annotations,
                                        sample_annotations)
            setup_annotation_data_by_qs(qs.filter(best_cohens_kappa=1),
                                        concordant_serie_annotations,
                                        concordant_sample_annotations)

            qs = SeriesTag.objects.filter(platform__specie=specie, is_active=True)
            series_tags[specie] = accumulate(count_by(
                ceil_date, qs.values_list('created_on', flat=True)))
            concordant_series_tags[specie] = accumulate(count_by(
                ceil_date, qs.exclude(agreed=None).values_list('created_on', flat=True)))

            qs = SampleTag.objects.filter(sample__platform__specie=specie, is_active=True)
            sample_tags[specie] = accumulate(count_by(
                ceil_date, qs.values_list('created_on', flat=True)))
            concordant_sample_tags[specie] = accumulate(count_by(
                ceil_date, qs.exclude(series_tag__agreed=None).values_list('created_on', flat=True)))

            qs = SerieValidation.objects.filter(ignored=False, by_incompetent=False)
            serie_validations[specie] = accumulate(count_by(
                ceil_date, qs.values_list('created_on', flat=True)))
            concordant_serie_validations[specie] = accumulate(count_by(
                ceil_date, qs.filter(best_kappa=1).values_list('created_on', flat=True)))

            qs = SampleValidation.objects\
                                 .filter(serie_validation__ignored=False,
                                         serie_validation__by_incompetent=False)

            sample_validations[specie] = accumulate(count_by(
                ceil_date, qs.values_list('created_on', flat=True)))
            concordant_sample_validations[specie] = accumulate(count_by(
                ceil_date,
                qs.filter(Q(serie_validation__best_kappa=1) | Q(concordant=True))
                  .values_list('created_on', flat=True)))


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
            'serie_annotations': serie_annotations,
            'sample_annotations': sample_annotations,
            'concordant_serie_annotations': concordant_serie_annotations,
            'concordant_sample_annotations': concordant_sample_annotations,
            'series_tags': series_tags,
            'sample_tags': sample_tags,
            'concordant_series_tags': concordant_series_tags,
            'concordant_sample_tags': concordant_sample_tags,
            'serie_validations': serie_validations,
            'sample_validations': sample_validations,
            'concordant_serie_validations': concordant_serie_validations,
            'concordant_sample_validations': concordant_sample_validations,
            'serie_tags_by_users': distribute_by_user_id(SeriesTag.objects.filter(is_active=True)),
            'sample_tags_by_users': distribute_by_user_id(SampleTag.objects.filter(is_active=True)),
            'serie_validations_by_users': distribute_by_user_id(SerieValidation.objects.filter(
                ignored=False, by_incompetent=False)),
            'sample_validations_by_users': distribute_by_user_id(SampleValidation.objects.filter(
                serie_validation__ignored=False,
                serie_validation__by_incompetent=False)),
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
        import ipdb; ipdb.set_trace()
        pass
