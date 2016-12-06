from funcy import zipdict
from handy.decorators import render_to

from django import forms
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

from .conf import redis_client


@render_to(template='dashboard.j2')
def dashboard(request):
    keys = ('core.stats.tags', 'core.stats.serie_annotations', 'core.stats.sample_annotations',
            'core.graph')
    return {
        'stats': zipdict(keys, redis_client.mget(*keys))
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

        User = get_user_model()  # noqa
        try:
            user = User._default_manager.get(email__iexact=email)
        except User.DoesNotExist:
            print 'dne'
            raise ValidationError('There is no registered user with this email.')
        if user.is_active:
            raise ValidationError('User with this email is already active. Just log in.')
        self.user = user
        return email
