from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm as _PasswordResetForm


class PasswordResetForm(_PasswordResetForm):
    """
    Custom PasswordResetForm to permit changing passwords for users without one.
    Also, shows an error if email is not found.
    """
    def clean_email(self):
        email = self.cleaned_data["email"]
        users = self.get_users(email)
        if not users:
            raise ValidationError('Unknwn email %s' % email)
        return email

    def get_users(self, email):
        """Allow users with inactive passwords to reset it"""
        return get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
