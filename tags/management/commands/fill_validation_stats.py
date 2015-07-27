from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.models import F
from tqdm import tqdm

from legacy.models import SeriesTag
from tags.models import SerieValidation, UserStats, ValidationJob
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

        if options['recalc']:
            SeriesTag.objects.all().update(agreed=None, fleiss_kappa=None)

        print '> Calculating serie validation stats...'
        qs = SerieValidation.objects.values_list('pk', 'samples_total').order_by('created_on')
        if not options['recalc']:
            qs = qs.filter(samples_total=None)

        for pk, samples_total in tqdm(qs):
            calc_validation_stats(pk, recalc=samples_total is not None)

        if options['recalc']:
            print '> Creating validation jobs...'
            ValidationJob.objects.all().delete()
            for st in SeriesTag.objects.filter(agreed=None).iterator():
                priority = st.fleiss_kappa - 1 if st.fleiss_kappa else 0
                ValidationJob.objects.create(series_tag=st, priority=priority)
