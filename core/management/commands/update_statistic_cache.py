from django.core.management import BaseCommand
from core.models import StatisticCache


class Command(BaseCommand):
    def handle(self, *args, **options):
        StatisticCache.objects.update_statistics()
