from handy.decorators import render_to, paginate, render_to_json

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect

from core.conf import redis_client
import tango
from .models import UserStats, Payment
from .tasks import redeem_earnings, donate_earnings


admin_required = user_passes_test(lambda u: u.is_superuser)


@admin_required
@render_to('users/stats.j2')
def stats(request):
    return {
        'users': User.objects.select_related('stats').exclude(stats=None)
                             .order_by('first_name', 'last_name')
    }


@admin_required
@render_to('users/accounting.j2')
@paginate('payments', 10)
def accounting(request):
    return {
        'payments': Payment.objects.order_by('-created_on')
                           .select_related('receiver', 'created_by')
    }


@render_to_json()
@admin_required
def account_info(request):
    return tango.account_info()


@login_required
@render_to('users/redeem.j2')
def redeem(request):
    if request.method == 'POST':
        if 'donate' in request.POST:
            donate_earnings(request.user.id)
            messages.success(request, 'Thank you very mush for your support')
            return redirect('redeem')
        else:
            # Mark redeem as in progress
            redis_client.setex('redeem:%d' % request.user.id, 60, 'active')
            redeem_earnings.delay(request.user.id)
            messages.success(request, 'Ordering a Tango Card for you')
            return redirect('redeem')

    last_payment = Payment.objects.filter(receiver_id=request.user.id) \
                          .order_by('created_on').last()

    return {
        'active': redis_client.get('redeem.samples:%d' % request.user.id),
        'stats': UserStats.objects.get(pk=request.user.id),
        'last_payment': last_payment
    }


@admin_required
@render_to('users/pay.j2')
def pay(request):
    receiver = User.objects.select_related('stats').get(pk=request.GET['user_id'])

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            redeem_earnings.delay(
                receiver_id=payment.receiver_id,
                amount=payment.amount,
                method=payment.method,
                sender_id=request.user.id,
            )
            messages.success(request, 'Ordering Tango card')
            return redirect('stats')
    else:
        payment = Payment(
            receiver=receiver,
            amount=receiver.stats.unpayed,
            method='Tango Card',
        )
        form = PaymentForm(instance=payment)

    return {
        'receiver': receiver,
        'form': form
    }


# A form

from django.forms import ModelForm, TextInput

class PaymentForm(ModelForm):
    def clean(self):
        # Check if there is not enough unpayed reward
        unpayed = self.cleaned_data['receiver'].stats.unpayed
        if unpayed < self.cleaned_data['amount']:
            self.add_error('amount', 'User has only %s unpayed reward' % unpayed)

    class Meta:
        model = Payment
        fields = ['receiver', 'amount', 'method']
        widgets = {'method': TextInput}
