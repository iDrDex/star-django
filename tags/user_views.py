from handy.decorators import render_to

from django.contrib import messages
from django.shortcuts import redirect

from core.conf import redis_client
from core.utils import admin_required, login_required
from legacy.models import AuthUser
from .models import UserStats, Payment, SAMPLE_REWARD
from .tasks import redeem_samples


@admin_required
@render_to('users/stats.j2')
def stats(request):
    return {
        'users': AuthUser.objects.select_related('stats').exclude(stats=None)
                                 .order_by('first_name', 'last_name')
    }


@login_required
@render_to('users/redeem.j2')
def redeem(request):
    if request.method == 'POST':
        # Mark redeem as in progress
        redis_client.setex('redeem.samples:%d' % request.user_data['id'], 60, 'active')
        redeem_samples.delay(request.user_data['id'])
        messages.success(request, 'Ordered a Tango Card for you')
        return redirect('redeem')

    return {
        'active': redis_client.get('redeem.samples:%d' % request.user_data['id']),
        'stats': UserStats.objects.get(pk=request.user_data['id']),
    }


@admin_required
@render_to('users/pay.j2')
def pay(request):
    receiver = AuthUser.objects.select_related('stats').get(pk=request.GET['user_id'])

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            redeem_samples.delay(
                receiver_id=payment.receiver_id,
                samples=payment.samples,
                method=payment.method,
                sender_id=request.user_data['id'],
            )

            messages.success(request, 'Saved payment')
            return redirect('stats')
    else:
        payment = Payment(
            receiver=receiver,
            samples=receiver.stats.samples_unpayed,
            amount=receiver.stats.amount_unpayed,
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
        # Keep this amount and samples in sync
        self.cleaned_data['amount'] = self.cleaned_data['samples'] * SAMPLE_REWARD
        # Check if there is not enough samples
        unpayed_samples = self.cleaned_data['receiver'].stats.samples_unpayed
        if unpayed_samples < self.cleaned_data['samples']:
            self.add_error('samples', 'User has only %d unpayed samples' % unpayed_samples)

    class Meta:
        model = Payment
        fields = ['receiver', 'samples', 'amount', 'method']
        widgets = {'method': TextInput}
