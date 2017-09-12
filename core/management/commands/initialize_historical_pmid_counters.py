from funcy import *  # noqa
from datetime import datetime, timedelta
from django.core.management import BaseCommand
from core.models import HistoricalCounter
from legacy.models import Series
from initialize_historical_counters import ceil_date, MONTHS, CURRENT_DATE, START_DATE, get_value


def convert_date(attr):
    month, day, year = attr.get('submission_date', 'Jan 1 1960').split()
    if month == 'Jans':
        month = 'Jan'
    return ceil_date(datetime(int(year), MONTHS.index(month) + 1, 1))


class Command(BaseCommand):
    def handle(self, *args, **options):
        group = group_values(
            [convert_date(attr), attr.get('pubmed_id', '').split('|\n|')]
            for attr in Series.objects.values_list('attrs', flat=True))

        uniq_pmids = set([])

        def count_uniq_pmids(pmids):
            uniq_pmids.update(set(flatten(pmids)))
            return len(uniq_pmids)

        pmids = dict(walk_values(count_uniq_pmids, sorted(group.items())))

        delta = CURRENT_DATE - START_DATE
        keys = sorted(set(ceil_date(START_DATE + timedelta(days=index * 20))
                          for index in range(delta.days / 20 + 1)))

        for index, date in enumerate(keys):
            hc = HistoricalCounter.objects.filter(created_on=date).first()
            if not hc:
                continue
            hc.counters['PMID'] = get_value(keys, index)(pmids)
            hc.save()
