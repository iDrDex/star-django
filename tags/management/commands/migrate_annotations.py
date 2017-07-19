from funcy import project
from tqdm import tqdm
from django.core.management.base import BaseCommand

from tags.models import SeriesTag, SerieValidation, RawSeriesAnnotation, RawSampleAnnotation, \
    ValidationJob


class Command(BaseCommand):
    help = 'Update canonical annotations'

    def handle(self, *args, **kwargs):
        # These are created by Dexter
        SeriesTag.objects.filter(created_by=None).update(created_by=1)
        SeriesTag.objects.filter(modified_by=None).update(modified_by=1)

        # RawSeriesAnnotation.objects.all().delete()

        source_to_canonical = {}
        st_to_raw = dict(RawSeriesAnnotation.objects.filter(from_series_tag__isnull=False)
                                            .values_list('from_series_tag', 'pk'))
        sv_to_raw = dict(RawSeriesAnnotation.objects.filter(from_validation__isnull=False)
                                            .values_list('from_validation', 'pk'))

        def dup_check(anno, canonical_id):
            key = (anno.series_id, anno.platform_id, anno.tag_id, anno.created_by_id)
            if key in source_to_canonical:
                return False, source_to_canonical[key]
            else:
                source_to_canonical[key] = canonical_id
                return True, canonical_id

        last_created_on = None
        for st in tqdm(SeriesTag.objects.prefetch_related('canonical'), 'annotations'):
            if st.is_active:
                is_active, canonical_id = dup_check(st, st.canonical.pk)
            else:
                is_active, canonical_id = False, st.canonical.pk
            last_created_on = st.created_on or last_created_on
            if st.pk in st_to_raw:
                continue
            anno = RawSeriesAnnotation.objects.create(
                from_series_tag=st,
                canonical_id=canonical_id,
                column=st.header or '',
                regex=st.regex or '',
                is_active=is_active,
                created_on=st.created_on or last_created_on,
                **project(st.__dict__, ['series_id', 'platform_id', 'tag_id',
                                        'created_by_id', 'modified_on', 'from_api', 'note'])
            )
            st_to_raw[st.pk] = anno.pk

            sample_tags = st.sample_tags.values_list('sample_id', 'annotation')
            RawSampleAnnotation.objects.bulk_create(
                RawSampleAnnotation(
                    series_annotation=anno,
                    sample_id=sample_id,
                    annotation=annotation or '',
                )
                for sample_id, annotation in sample_tags
            )

        qs = SerieValidation.objects.prefetch_related('series_tag__canonical').order_by('id')
        for sv in tqdm(qs, 'validations'):
            # validations without source, drop them
            if sv.series_tag is None:
                continue
            if sv.by_incompetent or sv.ignored or sv.on_demand:
                is_active = not sv.by_incompetent and not sv.ignored
                canonical_id = sv.series_tag.canonical.pk
            else:
                is_active, canonical_id = dup_check(sv, sv.series_tag.canonical.pk)
            if sv.pk in sv_to_raw:
                continue

            # Agreement fields
            agrees_with_id = None
            if sv.concordant:
                agrees_with_id = st_to_raw[sv.series_tag_id]
            elif sv.agrees_with_id:
                agrees_with_id = sv_to_raw[sv.agrees_with_id]
            if agrees_with_id:
                RawSeriesAnnotation.objects.filter(pk=agrees_with_id).update(agreed=True)

            anno = RawSeriesAnnotation.objects.create(
                from_validation=sv,
                canonical_id=canonical_id,
                is_active=is_active,
                agrees_with_id=agrees_with_id,
                **project(sv.__dict__, [
                    'series_id', 'platform_id', 'tag_id', 'column', 'regex',
                    'created_on', 'created_by_id', 'modified_on',
                    'from_api', 'note', 'on_demand', 'ignored', 'by_incompetent', 'best_kappa'])
            )
            sv_to_raw[sv.pk] = anno.pk

            sample_validations = sv.sample_validations.values_list('sample_id', 'annotation')
            RawSampleAnnotation.objects.bulk_create(
                RawSampleAnnotation(
                    series_annotation=anno,
                    sample_id=sample_id,
                    annotation=annotation,
                )
                for sample_id, annotation in sample_validations
            )

        # Update validation jobs
        for job in tqdm(ValidationJob.objects.filter(annotation=None), 'jobs'):
            job.annotation_id = st_to_raw[job.series_tag_id]
            job.save()
