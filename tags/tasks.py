import logging
from celery import shared_task
from django.db import transaction
from django.db.models import F

from core.conf import redis_client
from .models import SerieValidation, UserStats, ValidationJob, Payment, PaymentState, SAMPLE_REWARD


logger = logging.getLogger(__name__)


@shared_task(acks_late=True)
@transaction.atomic('legacy')
def calc_validation_stats(serie_validation_pk):
    serie_validation = SerieValidation.objects.select_for_update().get(pk=serie_validation_pk)
    # Guard from double update, so that user stats won't be messed up
    if serie_validation.samples_total is not None:
        return

    sample_validations = serie_validation.sample_validations.all()
    tags_by_sample = {obj.sample_id: obj for obj in serie_validation.series_tag.sample_tags.all()}

    # Check if samples set is the same
    if set(tags_by_sample) != set(sv.sample_id for sv in sample_validations):
        logger.error('Samples sets differ for serie validation %s and its annotation',
                     serie_validation_pk)
        return

    for sv in sample_validations:
        sample_tag = tags_by_sample[sv.sample_id]
        sv.concordant = sv.annotation == (sample_tag.annotation or '')
        sv.save()

    serie_validation.samples_total = len(sample_validations)
    serie_validation.samples_concordant = sum(s.concordant for s in sample_validations)
    if sample_validations:
        serie_validation.samples_concordancy \
            = float(serie_validation.samples_concordant) / serie_validation.samples_total
    serie_validation.save()

    # Update validating user stats
    stats, _ = UserStats.objects.select_for_update() \
        .get_or_create(user_id=serie_validation.created_by_id)
    stats.serie_validations += 1
    stats.sample_validations += serie_validation.samples_total
    if serie_validation.concordant:
        stats.serie_validations_concordant += 1
    stats.sample_validations_concordant += serie_validation.samples_concordant

    # Pay for all samples, but only if entire serie is concordant
    if serie_validation.concordant:
        stats.samples_to_pay_for += serie_validation.samples_total
    stats.save()

    # Update annotation author payment stats
    if serie_validation.concordant:
        author_id = serie_validation.series_tag.created_by_id
        author_stats, _ = UserStats.objects.select_for_update().get_or_create(user_id=author_id)
        author_stats.samples_to_pay_for += serie_validation.samples_total
        author_stats.save()

    # Reschedule validation if not concordant
    if not serie_validation.concordant:
        _reschedule_validation(serie_validation)


def _reschedule_validation(serie_validation):
    failed = SerieValidation.objects.filter(series_tag=serie_validation.series_tag).count()
    if failed >= 3:
        # TODO: create user interface to see problematic series tags
        logger.info('Failed validating %s serie tag %d times',
                    serie_validation.series_tag_id, failed)
        return

    ValidationJob.objects.create(series_tag=serie_validation.series_tag)


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
