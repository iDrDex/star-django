# TODO: remove this once series_attribute and sample_attribute tables are gone

from tqdm import tqdm
from funcy import cut_prefix
from django.core.management.base import BaseCommand
from django.db import transaction

from legacy.models import Series, SeriesAttribute, SampleAttribute


class Command(BaseCommand):
    help = "Move series and samples attributes from separate tables to JSON"

    def handle(self, *args, **options):
        series = Series.objects.filter(attrs={})
        for serie in tqdm(series):
            fill_serie_data(serie)


@transaction.atomic
def fill_serie_data(serie):
    attrs = dict(SeriesAttribute.objects.filter(series=serie)
                                .values_list('attribute_name', 'attribute_value'))
    attrs = {cut_prefix(name, 'series_'): value for name, value in attrs.items()}
    serie.attrs = attrs
    serie.save()

    for sample in serie.samples.all():
        attrs = dict(SampleAttribute.objects.filter(sample=sample)
                                    .values_list('attribute_name', 'attribute_value'))
        attrs = {cut_prefix(name, 'sample_'): value for name, value in attrs.items()}
        sample.attrs = attrs
        sample.save()
