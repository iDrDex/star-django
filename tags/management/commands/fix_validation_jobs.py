from django.core.management.base import BaseCommand
from tqdm import tqdm

from tags.models import SeriesAnnotation, ValidationJob


class Command(BaseCommand):
    help = 'Fixes validation jobs'

    def handle(self, **options):
        has_jobs = set(ValidationJob.objects.values_list('annotation_id', flat=True))
        annos = SeriesAnnotation.objects.values_list('pk', 'best_cohens_kappa')
        need_jobs = {pk for pk, k in annos if k != 1}

        missing = need_jobs - has_jobs
        if missing:
            print('> Going to create %d validation jobs...' % len(missing))
            for pk in tqdm(missing):
                ValidationJob.objects.create(annotation_id=pk)

        extra = has_jobs - need_jobs
        if extra:
            print('> Going to delete %d validation jobs...' % len(extra))
            ValidationJob.objects.filter(annotation__in=extra).delete()
