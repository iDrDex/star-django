from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import F
from tqdm import tqdm

from tags.models import SerieValidation, UserStats
from tags.tasks import calc_validation_stats


class Command(BaseCommand):
    help = 'Fills validation stats'

    option_list = BaseCommand.option_list + (
        make_option(
            '--full',
            action='store_true',
            dest='full',
            default=False,
            help='Delete old stats before starting'
        ),
        make_option(
            '--recalc',
            action='store_true',
            dest='recalc',
            default=False,
        ),
    )

    def handle(self, *args, **options):
        if options['full']:
            SerieValidation.objects.update(
                samples_total=None,
                samples_concordant=None,
                samples_concordancy=None
            )
            UserStats.objects.update(
                serie_validations=0,
                sample_validations=0,
                serie_validations_concordant=0,
                sample_validations_concordant=0,
                samples_to_pay_for=0,
            )

            # Delete cheat validations
            SerieValidation.objects.filter(series_tag__created_by=F('created_by')).delete()

        qs = SerieValidation.objects.values_list('pk', 'samples_total')
        if not options['recalc']:
            qs = qs.filter(samples_total=None)
        for pk, samples_total in tqdm(qs):
            calc_validation_stats(pk, recalc=samples_total is not None)
