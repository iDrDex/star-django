from django.core.management import BaseCommand
from core.models import HistoryStatisticCache


class Command(BaseCommand):
    def handle(self, *args, **options):
        HistoryStatisticCache.objects.update_history()
