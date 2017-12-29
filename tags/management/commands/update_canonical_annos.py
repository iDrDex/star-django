from django.core.management.base import BaseCommand
from tqdm import tqdm

from tags.models import SeriesAnnotation
from tags.annotate_core import update_canonical


class Command(BaseCommand):
    help = 'Update canonical annotations'

    def handle(self, *args, **kwargs):
        import sys, ipdb, traceback  # noqa

        def info(type, value, tb):
            traceback.print_exception(type, value, tb)
            print()
            ipdb.pm()
        sys.excepthook = info

        # Update
        pks = SeriesAnnotation.objects.values_list('pk', flat=True)
        for pk in tqdm(pks):
            update_canonical(pk)
