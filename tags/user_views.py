from decimal import Decimal
from handy.decorators import render_to

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect

from core.utils import admin_required
from legacy.models import AuthUser
from .models import UserStats, Payment


@admin_required
@render_to('tags/stats.j2')
def stats(request):
    return {
        'users': AuthUser.objects.select_related('stats').exclude(stats=None)
                                 .order_by('first_name', 'last_name')
    }


@admin_required
@render_to('tags/pay.j2')
def pay(request):
    receiver = AuthUser.objects.select_related('stats').get(pk=request.GET['user_id'])

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            save_payment(request, form)
            messages.success(request, 'Saved payment')
            return redirect('stats')
    else:
        payment = Payment(
            receiver=receiver,
            samples=receiver.stats.samples_unpayed,
            amount=receiver.stats.samples_unpayed * Decimal('0.05'),
            method='Tango Card',
        )
        form = PaymentForm(instance=payment)

    return {
        'receiver': receiver,
        'form': form
    }


@transaction.atomic
def save_payment(request, form):
    payment = form.save(commit=False)
    payment.created_by_id = request.user_data['id']
    payment.save()

    UserStats.objects.filter(user_id=form.cleaned_data['receiver']) \
        .update(samples_payed=F('samples_payed') + form.cleaned_data['samples'])


# A form

from django.forms import ModelForm, TextInput

class PaymentForm(ModelForm):
    def clean(self):
        unpayed_samples = self.cleaned_data['receiver'].stats.samples_unpayed
        if unpayed_samples < self.cleaned_data['samples']:
            self.add_error('samples', 'User has only %d unpayed samples' % unpayed_samples)

    class Meta:
        model = Payment
        fields = ['receiver', 'samples', 'amount', 'method']
        widgets = {'method': TextInput}
