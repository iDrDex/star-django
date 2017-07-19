import logging

from celery import shared_task
from django.db import transaction
from django.db.models import F

from core.conf import redis_client
from .models import Payment, PaymentState, UserStats


logger = logging.getLogger(__name__)


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
