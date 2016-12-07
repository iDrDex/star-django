from django.core.management.base import BaseCommand

from legacy.models import Series


class Command(BaseCommand):
    help = 'Recalc series calculated fields'

    def handle(self, **options):
        for s in Series.objects.iterator():
            s.save()
