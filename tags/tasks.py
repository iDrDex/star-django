# TODO: separate idempotent parts into separate file?
from operator import attrgetter
from collections import defaultdict
import logging

import numpy as np
from statsmodels.stats.inter_rater import fleiss_kappa, cohens_kappa
from funcy import group_by, cat, distinct, first, chain
from celery import shared_task
from django.db import transaction
from django.db.models import F

from core.conf import redis_client
from .models import (SeriesTag, SerieValidation, SampleValidation,
                     UserStats, ValidationJob, Payment, PaymentState)


logger = logging.getLogger(__name__)


# TODO: get rid of flag
@shared_task(acks_late=True)
def validation_workflow(sv_id, is_new=True):
    series_tag_id = SerieValidation.objects.get(pk=sv_id).series_tag_id

    if is_new:
        calc_validation_stats(sv_id)
    else:
        validations = SerieValidation.objects.filter(series_tag=series_tag_id, pk__gte=sv_id) \
                                             .order_by('pk')
        for v in validations:
            calc_validation_stats(v.pk, recalc=True)

    update_canonical_annotation(series_tag_id)


# TODO: get rid of recalc flag, separate function into 2 or 3:
#           - idempotent stats calculation
#           - stats and reschedule
@shared_task(acks_late=True)
@transaction.atomic
def calc_validation_stats(serie_validation_pk, recalc=False):
    serie_validation = SerieValidation.objects.select_for_update().get(pk=serie_validation_pk)
    # Guard from double update, so that user stats won't be messed up
    if not recalc and serie_validation.samples_total is not None:
        return
    series_tag = serie_validation.series_tag
    if not series_tag:
        return

    # Compare to annotation
    sample_validations = serie_validation.sample_validations.all()
    sample_annotations = series_tag.sample_tags.all()

    if set(r.sample_id for r in sample_validations) \
            != set(r.sample_id for r in sample_annotations):
        logger.error("Sample sets mismatch for validation %d" % serie_validation_pk)
        # It's either bug when making annotation or samples set really changed
        series_tag.is_active = False
        series_tag.save()
        # TODO: notify annotation author to redo it
        return

    _fill_concordancy(sample_validations, sample_annotations)

    # Fill serie validation stats
    serie_validation.samples_total = len(sample_validations)
    serie_validation.samples_concordant = sum(s.concordant for s in sample_validations)
    serie_validation.annotation_kappa = _cohens_kappa(sample_validations, sample_annotations)

    # Compare to other validations
    earlier_validations = series_tag.validations.filter(pk__lt=serie_validation_pk, ignored=False) \
                                    .order_by('pk')
    # TODO: use .prefetch_related()
    earlier_sample_validations = group_by(
        lambda v: v.serie_validation_id,
        SampleValidation.objects.filter(serie_validation__in=earlier_validations)
    )

    if not serie_validation.concordant:
        serie_validation.agrees_with = first(
            v for v in earlier_validations
            if v.created_by_id != serie_validation.created_by_id
            and is_samples_concordant(earlier_sample_validations[v.pk], sample_validations)
        )

    # NOTE: this includes kappas against your prev validations
    serie_validation.best_kappa = max(chain(
        [serie_validation.annotation_kappa],
        (_cohens_kappa(sample_validations, sv) for sv in earlier_sample_validations.values())
    ))
    serie_validation.save()

    # Calculate fleiss kappa for all existing annotations/validations
    annotation_sets = [sample_annotations, sample_validations] \
        + earlier_sample_validations.values()
    series_tag.fleiss_kappa = _fleiss_kappa(annotation_sets)
    if not serie_validation.on_demand and not serie_validation.ignored \
            and (serie_validation.concordant or serie_validation.agrees_with):
        series_tag.agreed = earlier_validations.count() + 1
    series_tag.save()

    # TODO: make this separate task ?
    if not recalc and not serie_validation.on_demand and not serie_validation.by_incompetent:
        _update_user_stats(serie_validation)  # including payment ones

    # TODO: make this separate task ?
    # Reschedule validation if no agreement found
    if not series_tag.agreed and not recalc and not serie_validation.on_demand \
            and not serie_validation.by_incompetent:
        # Schedule revalidations with priority < 0, that's what new validations have,
        # to phase out garbage earlier
        _reschedule_validation(serie_validation, priority=series_tag.fleiss_kappa - 1)


def _fill_concordancy(sample_validations, reference):
    tags_by_sample = {obj.sample_id: obj for obj in reference}

    for sv in sample_validations:
        sample_tag = tags_by_sample[sv.sample_id]
        sv.concordant = sv.annotation == (sample_tag.annotation or '')
        sv.save()


def _update_user_stats(serie_validation):
    def lock_author_stats(work):
        stats, _ = UserStats.objects.select_for_update().get_or_create(user_id=work.created_by_id)
        return stats

    # Update validating user stats
    stats = lock_author_stats(serie_validation)
    stats.serie_validations += 1
    stats.sample_validations += serie_validation.samples_total
    if serie_validation.concordant:
        stats.serie_validations_concordant += 1
    stats.sample_validations_concordant += serie_validation.samples_concordant

    # Pay for all samples, but only if entire serie is concordant
    if serie_validation.concordant or serie_validation.agrees_with:
        stats.earn_validations(serie_validation.samples_total)
    stats.save()

    # Update annotation author payment stats
    if serie_validation.concordant:
        author_stats = lock_author_stats(serie_validation.series_tag)
        author_stats.earn_annotations(serie_validation.samples_total)
        author_stats.save()

    # Update the author of earlier matching validation
    if serie_validation.agrees_with:
        author_stats = lock_author_stats(serie_validation.agrees_with)
        author_stats.earn_validations(serie_validation.samples_total)
        author_stats.save()


def _reschedule_validation(serie_validation, priority=None):
    failed = SerieValidation.objects \
        .filter(series_tag=serie_validation.series_tag, on_demand=False).count()
    if failed >= 5:
        logger.info('Failed validating %s serie tag %d times',
                    serie_validation.series_tag_id, failed)
        return

    ValidationJob.objects.create(series_tag=serie_validation.series_tag, priority=priority)


def is_samples_concordant(sample_annos1, sample_annos2):
    ref = {obj.sample_id: obj for obj in sample_annos1}
    return all((ref[v.sample_id].annotation or '') == (v.annotation or '')
               for v in sample_annos2)


def _fleiss_kappa(sample_sets):
    all_samples_annos = cat(sample_sets)
    categories = distinct(sv.annotation or '' for sv in all_samples_annos)
    category_index = {c: i for i, c in enumerate(categories)}

    stats = defaultdict(lambda: [0] * len(categories))
    for sv in all_samples_annos:
        stats[sv.sample_id][category_index[sv.annotation or '']] += 1

    return fleiss_kappa(stats.values())

def _cohens_kappa(annos1, annos2):
    assert set(s.sample_id for s in annos1) == set(s.sample_id for s in annos2)

    categories = distinct(sv.annotation or '' for sv in chain(annos1, annos2))
    category_index = {c: i for i, c in enumerate(categories)}

    table = np.zeros((len(categories), len(categories)))
    annos1 = sorted(annos1, key=attrgetter('sample_id'))
    annos2 = sorted(annos2, key=attrgetter('sample_id'))
    for sv1, sv2 in zip(annos1, annos2):
        table[category_index[sv1.annotation or ''], category_index[sv2.annotation or '']] += 1

    return cohens_kappa(table, return_results=False)


@shared_task(acks_late=True)
@transaction.atomic
def update_canonical_annotation(series_tag_pk):
    st = SeriesTag.objects.select_for_update().get(pk=series_tag_pk)
    validations = st.validations.filter(ignored=False).order_by('pk')

    best_cohens_kappa = max(v.best_kappa for v in validations) if validations else None

    # Update samples to be canonical
    source = first(v for v in validations if v.concordant or v.agrees_with) \
        or first(v for v in validations if v.best_kappa == best_cohens_kappa)

    if source:
        current_samples = st.canonical.sample_annotations.all()
        source_samples = source.sample_validations.all()
        # If samples set changed then just replace everything
        if set(o.sample_id for o in current_samples) != set(o.sample_id for o in source_samples):
            current_samples.delete()
            st.canonical.fill_samples(source_samples)
        elif not is_samples_concordant(current_samples, source_samples):
            anno_by_sample = {obj.sample_id: obj.annotation for obj in source_samples}
            for sample_anno in current_samples:
                sample_anno.annotation = anno_by_sample[sample_anno.sample_id]
                sample_anno.save()

    # Update canonical stats
    st.canonical.header = source.column if source else st.header
    st.canonical.regex = source.regex if source else (st.regex or '')
    st.canonical.annotations = validations.count() + 1
    st.canonical.authors = len(set(v.created_by_id for v in validations) | {st.created_by_id})
    st.canonical.fleiss_kappa = st.fleiss_kappa
    st.canonical.best_cohens_kappa = best_cohens_kappa
    st.canonical.save()


from tango import place_order

@shared_task(acks_late=True)
def redeem_earnings(receiver_id=None, amount=None, method='Tango Card API', sender_id=None):
    # We need to create a pending payment in a separate transaction to be safe from double card
    # ordering. This way even if we fail at any moment later payment and new stats will persist
    # and won't allow us to issue a new card for same work.
    with transaction.atomic():
        stats = UserStats.objects.select_for_update().get(user_id=receiver_id)
        # If 2 redeem attempts are tried simultaneously than first one will lock samples,
        # and second one should just do nothing.
        amount = amount or stats.unpayed
        if not amount:
            logger.error('Nothing to redeem for user %d', receiver_id)
            return
        if amount > stats.unpayed:
            logger.error('Trying to redeem %s but user %d has only %s',
                         amount, receiver_id, stats.unpayed)
            return

        # Create pending payment
        payment = Payment.objects.create(
            receiver_id=receiver_id,
            amount=amount,
            method=method,
            created_by_id=sender_id or receiver_id,
            state=PaymentState.PENDING,
        )

        # Update stats
        stats.payed += amount
        stats.save()

    with transaction.atomic():
        # Relock this so that nobody will alter or remove it concurrently
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        if payment.state != PaymentState.PENDING:
            return
        user = payment.receiver

        try:
            result = place_order(
                name='%s %s' % (user.first_name, user.last_name),
                email=user.email,
                amount=payment.amount,
            )
        except Exception as e:
            result = {
                'success': False,
                'exception_class': e.__class__.__name__,
                'exception_args': getattr(e, 'args', ()),
            }

        # Update payment
        payment.state = PaymentState.DONE if result['success'] else PaymentState.FAILED
        payment.extra = result
        payment.save()

        # Restore samples stats as they were before payment lock,
        # so that another attempt could be made.
        if not result['success']:
            UserStats.objects.filter(user_id=receiver_id) \
                .update(payed=F('payed') - payment.amount)

    # Remove in-progress flag
    redis_client.delete('redeem:%d' % receiver_id)


@transaction.atomic
def donate_earnings(user_id):
    stats = UserStats.objects.select_for_update().get(user_id=user_id)
    amount = stats.unpayed

    if not amount:
        return

    # Create payment to log all operations
    Payment.objects.create(
        receiver_id=user_id,
        amount=amount,
        method='Donate',
        created_by_id=user_id,
        state=PaymentState.DONE,
    )

    stats.payed += amount
    stats.save()
