from funcy import group_by
from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from tags.models import RawSeriesAnnotation, SeriesAnnotation


class Command(BaseCommand):
    def handle(self, **options):
        SeriesAnnotation.objects.filter(annotations__gt=0).update(is_active=True)

        qs = RawSeriesAnnotation.objects.order_by('id')
        by_canonical = group_by(lambda a: a.canonical_id, qs)

        for anno in tqdm(qs):
            if anno.ignored or anno.by_incompetent:
                continue
            last_anno = by_canonical[anno.canonical_id][-1]
            if not samples_match(anno, last_anno):
                anno.is_active = False
                anno.obsolete = True
                anno.save()
            else:
                anno.obsolete = False
                try:
                    anno.is_active = True
                    anno.save()
                except IntegrityError:
                    anno.is_active = False
                    anno.note += '# dup'
                    anno.save()


def samples_match(anno1, anno2):
    ref1 = {s.sample_id for s in anno1.sample_annotations.all()}
    ref2 = {s.sample_id for s in anno2.sample_annotations.all()}
    return ref1 == ref2
