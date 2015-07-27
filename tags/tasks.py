from collections import defaultdict
import logging

from funcy import group_by, cat, distinct
from celery import shared_task
from django.db import transaction
from django.db.models import F

from core.conf import redis_client
from .models import (SerieValidation, SampleValidation,
                     UserStats, ValidationJob, Payment, PaymentState, SAMPLE_REWARD)


logger = logging.getLogger(__name__)


@shared_task(acks_late=True)
@transaction.atomic('legacy')
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
        series_tag.obsolete = 'T'  # web2py messy booleans
        series_tag.save()
        # TODO: notify annotation author to redo it
        return

    _fill_concordancy(sample_validations, sample_annotations)

    serie_validation.samples_total = len(sample_validations)
    serie_validation.samples_concordant = sum(s.concordant for s in sample_validations)
    serie_validation.save()

    if serie_validation.concordant:
        earlier_validations = series_tag.validations.filter(pk__lt=serie_validation_pk)
        series_tag.agreed = earlier_validations.count() + 1
        series_tag.save()

    # Compare to other validations
    if not serie_validation.concordant:
        earlier_validations = series_tag.validations.filter(pk__lt=serie_validation_pk)
        earlier_sample_validations = group_by(
            lambda v: v.serie_validation_id,
            SampleValidation.objects.filter(serie_validation__in=earlier_validations)
        )
        for validation in earlier_validations:
            if is_samples_concordant(earlier_sample_validations[validation.pk], sample_validations):
                series_tag.agreed = len(earlier_validations) + 1
                series_tag.save()
                serie_validation.agrees_with = validation
                serie_validation.save()
                # TODO: generate a new SeriesTag from matching validations
                _generate_agreement_annotation(series_tag, serie_validation)
                break
        else:
            # Calculate fleiss kappa for all existing annotations/validations
            annotation_sets = [sample_annotations, sample_validations] \
                + earlier_sample_validations.values()
            series_tag.fleiss_kappa = annotations_similarity(annotation_sets)
            series_tag.save()

    if not recalc:
        _update_user_stats(serie_validation)  # including payment ones

    # Reschedule validation if no agreement found
    if not series_tag.agreed and not recalc:
        # Schedule revalidations with priority < 0, that's what new validations have,
        # to phase out garbage earlier
        _reschedule_validation(serie_validation, priority=series_tag.fleiss_kappa - 1)


def _fill_concordancy(sample_validations, reference):
    tags_by_sample = {obj.sample_id: obj for obj in reference}

    for sv in sample_validations:
        sample_tag = tags_by_sample[sv.sample_id]
        sv.concordant = sv.annotation == (sample_tag.annotation or '')
        sv.save()


def _generate_agreement_annotation(original_series_tag, serie_validation):
    pass


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
        stats.samples_to_pay_for += serie_validation.samples_total
    stats.save()

    # Update annotation author payment stats
    if serie_validation.concordant:
        author_stats = lock_author_stats(serie_validation.series_tag)
        author_stats.samples_to_pay_for += serie_validation.samples_total
        author_stats.save()

    # Update the author of earlier matching validation
    if serie_validation.agrees_with:
        author_stats = lock_author_stats(serie_validation.agrees_with)
        author_stats.samples_to_pay_for += serie_validation.samples_total
        author_stats.save()


def _reschedule_validation(serie_validation, priority=None):
    failed = SerieValidation.objects.filter(series_tag=serie_validation.series_tag).count()
    if failed >= 5:
        # TODO: create user interface to see problematic series tags
        logger.info('Failed validating %s serie tag %d times',
                    serie_validation.series_tag_id, failed)
        return

    ValidationJob.objects.create(series_tag=serie_validation.series_tag, priority=priority)


def is_samples_concordant(sample_annos1, sample_annos2):
    ref = {obj.sample_id: obj for obj in sample_annos1}
    return all((ref[v.sample_id].annotation or '') == (v.annotation or '')
               for v in sample_annos2)


def annotations_similarity(sample_sets):
    from statsmodels.stats.inter_rater import fleiss_kappa

    all_samples_annos = cat(sample_sets)
    categories = distinct(sv.annotation or '' for sv in all_samples_annos)
    category_index = {c: i for i, c in enumerate(categories)}

    stats = defaultdict(lambda: [0] * len(categories))
    for sv in all_samples_annos:
        stats[sv.sample_id][category_index[sv.annotation or '']] += 1

    return fleiss_kappa(stats.values())


from tango import place_order

@shared_task(acks_late=True)
def redeem_samples(receiver_id=None, samples=None, method='Tango Card API', sender_id=None):
    # We need to create a pending payment in a separate transaction to be safe from double card
    # ordering. This way even if we fail at any moment later payment and new stats will persist
    # and won't allow us to issue a new card for same work.
    with transaction.atomic('legacy'):
        stats = UserStats.objects.select_for_update().get(user_id=receiver_id)
        # If 2 redeem attempts are tried simultaneously than first one will lock samples,
        # and second one should just do nothing.
        samples = samples or stats.samples_unpayed
        if not samples:
            logger.error('Nothing to redeem for user %d', receiver_id)
            return
        if samples > stats.samples_unpayed:
            logger.error('Trying to redeem %d samples but user %d has only %d',
                         samples, receiver_id, stats.samples_unpayed)
            return

        # Create pending payment
        payment = Payment.objects.create(
            receiver_id=receiver_id,
            samples=samples,
            amount=samples * SAMPLE_REWARD,
            method=method,
            created_by_id=sender_id or receiver_id,
            state=PaymentState.PENDING,
        )

        # Update stats
        stats.samples_payed += samples
        stats.save()

    with transaction.atomic('legacy'):
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
                .update(samples_payed=F('samples_payed') - payment.samples)

    # Remove in-progress flag
    redis_client.delete('redeem.samples:%d' % receiver_id)


@transaction.atomic('legacy')
def donate_samples(user_id):
    stats = UserStats.objects.select_for_update().get(user_id=user_id)
    samples = stats.samples_unpayed

    if not samples:
        return

    # Create payment to log all operations
    Payment.objects.create(
        receiver_id=user_id,
        samples=samples,
        amount=samples * SAMPLE_REWARD,
        method='Donate',
        created_by_id=user_id,
        state=PaymentState.DONE,
    )

    stats.samples_payed += samples
    stats.save()
