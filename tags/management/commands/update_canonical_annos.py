from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from tags.models import SeriesAnnotation, SeriesTag
# from tags.tasks import update_canonical_annotation


class Command(BaseCommand):
    help = 'Update canonical annotations'

    def handle(self, *args, **kwargs):
        # Create missing
        missing_pks = set(SeriesTag.objects.values_list('pk', flat=True)) \
            - set(SeriesAnnotation.objects.values_list('series_tag_id', flat=True))
        if missing_pks:
            print '> Going to create %d missing canonical annotations...' % len(missing_pks)  # noqa
            for pk in tqdm(missing_pks):
                create_canonical_anno(pk)

        # # Update
        # pks = SeriesAnnotation.objects.values_list('series_tag_id', flat=True)
        # print '> Going to update %d canonical annotations...' % len(pks)  # noqa
        # for pk in tqdm(pks):
        #     update_canonical_annotation(pk)


@transaction.atomic
def create_canonical_anno(series_tag_pk):
    st = SeriesTag.objects.get(pk=series_tag_pk)
    sample_tags = st.sample_tags.values_list('sample_id', 'annotation')

    # Create canonical annotation
    sa = create_from_series_tag(st)
    sa.fill_samples(sample_tags)


def create_from_series_tag(st):
    return SeriesAnnotation.objects.create(
        series_tag_id=st.id,
        series_id=st.series_id, platform_id=st.platform_id, tag_id=st.tag_id,
        column=st.header, regex=st.regex or '',
        annotations=1, authors=1
    )
