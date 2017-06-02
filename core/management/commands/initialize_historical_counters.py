from funcy import *
from django.core.management import BaseCommand
from core.models import HistoricalCounter


class Command(BaseCommand):
    def _gather_series(self):
        from legacy.models import Series

        def extract_year(serie):
            return serie.attrs['submission_date'].split(' ')[2]

        def extract_month(serie):
            month = serie.attrs['submission_date'].split(' ')[0]
            if month == 'Jans':
                return Jan
            return month

        series = walk_values(partial(count_by, extract_month),
            group_by(extract_year,
                     Series.objects.all()))

        years = sorted(series.keys())
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        for year in years:
            for index, month in enumerate(months):
                source_year = str(int(year) - 1) if index == 0 else year
                source_month = months[index - 1]
                series[year][month] += series[source_year][source_month]

        return series

    def handle(self, *args, **options):
        series = self._gather_series()

        import ipdb; ipdb.set_trace()
        pass
