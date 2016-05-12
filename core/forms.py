from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm as _PasswordResetForm
from registration.forms import RegistrationForm


class MyRegistrationForm(RegistrationForm):
    error_css_class = 'error'

    class Meta(RegistrationForm.Meta):
        fields = [
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super(MyRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        users = get_user_model()._default_manager.filter(email__iexact=email)
        if users.exists():
            raise ValidationError('Email is aready in use.')
        return email

    def save(self, commit=True):
        user = super(MyRegistrationForm, self).save(commit=commit)
        user.username = user.email
        return user


class PasswordResetForm(_PasswordResetForm):
    """
    Custom PasswordResetForm to permit changing passwords for users without one.
    Also, shows an error if email is not found.
    """
    def clean_email(self):
        email = self.cleaned_data["email"]
        users = self.get_users(email)
        if not users:
            raise ValidationError('Unknown email %s' % email)
        return email

    def get_users(self, email):
        """Allow users with inactive passwords to reset it"""
        return get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
