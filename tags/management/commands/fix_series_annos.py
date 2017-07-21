from funcy import group_by
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from tags.models import RawSeriesAnnotation, SeriesAnnotation
from tags.annotate_core import is_samples_concordant


class Command(BaseCommand):
    def handle(self, **options):
        SeriesAnnotation.objects.filter(annotations__gt=0).update(is_active=True)

        qs = RawSeriesAnnotation.objects.filter(is_active=False, ignored=False) \
                                        .prefetch_related('sample_annotations') \
                                        .order_by('id')
        by_canonical = group_by(lambda a: a.canonical_id, qs)

        for anno in tqdm(qs):
            if anno.ignored or anno.by_incompetent:
                continue
            later_annos = [a for a in by_canonical[anno.canonical_id] if a.pk > anno.pk]
            if not all(is_samples_concordant(anno, a) for a in later_annos):
                anno.obsolete = True
                anno.save()
            else:
                try:
                    anno.is_active = True
                    anno.save()
                except IntegrityError:
                    anno.is_active = False
                    anno.note += '# dup'
                    anno.save()
