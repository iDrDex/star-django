from handy.decorators import render_to

from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from .models import StatisticCache, HistoricalCounter, User
from .conf import redis_client


@render_to(template='dashboard.j2')
def dashboard(request):
    return {
        'stats': dict(StatisticCache.objects.values_list('slug', 'count')),
        'graph': (redis_client.get('core.graph') or b'').decode(),
    }


from registration.backends.hmac.views import RegistrationView


@render_to(template='registration/reactivate.j2')
def reactivate(request):
    if request.method == 'POST':
        form = ReactivateForm(request.POST)
        if form.is_valid():
            view = RegistrationView(request=request)
            view.send_activation_email(form.user)
            return redirect(reactivate_sent)
    else:
        form = ReactivateForm()
    return {'form': form}


@render_to(template='registration/reactivate_sent.j2')
def reactivate_sent(request):
    return {}


class ReactivateForm(forms.Form):
    error_css_class = 'error'
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data.get('email')

        try:
            user = User._default_manager.get(email__iexact=email)
        except User.DoesNotExist:
            raise ValidationError('There is no registered user with this email.')
        if user.is_active:
            raise ValidationError('User with this email is already active. Just log in.')
        self.user = user
        return email

def format_username(u):
    text = '{first_name} {last_name}'.format(**u)
    return text if text != ' ' else u['pk']

@render_to(template='stats/stats.j2')
def stats(request):
    data = [
        [h.created_on.strftime('%Y-%m-%d'), h.counters]
        for h in HistoricalCounter.objects.all()
    ]
    users = {
        u['pk']: format_username(u)
        for u in User.objects.values('pk', 'first_name', 'last_name')
    }
    return {
        'data': data,
        'users': users,
    }
