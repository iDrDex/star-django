from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from legacy.models import SeriesTag
from tags.models import SerieAnnotation
from tags.tasks import update_canonical_annotation


class Command(BaseCommand):
    help = 'Update canonical annotations'

    def handle(self, *args, **kwargs):
        # Create missing
        missing_pks = set(SeriesTag.objects.exclude(obsolete='T').values_list('pk', flat=True)) \
            - set(SerieAnnotation.objects.values_list('series_tag_id', flat=True))
        if missing_pks:
            print '> Going to create %d missing canonical annotations...' % len(missing_pks)  # noqa
            for pk in tqdm(missing_pks):
                create_canonical_anno(pk)

        # Update
        pks = SerieAnnotation.objects.values_list('series_tag_id', flat=True)
        print '> Going to update %d canonical annotations...' % len(pks)  # noqa
        for pk in tqdm(pks):
            update_canonical_annotation(pk)


@transaction.atomic('legacy')
def create_canonical_anno(series_tag_pk):
    st = SeriesTag.objects.get(pk=series_tag_pk)
    sample_tags = st.sample_tags.all()

    # Create canonical annotation
    sa = SerieAnnotation.create_from_series_tag(st)
    sa.fill_samples(sample_tags)
