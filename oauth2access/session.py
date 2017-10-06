import django
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from requests_oauthlib import OAuth2Session

from .models import ServiceToken


# Changed from method to property
if django.VERSION >= (1, 10):
    is_authenticated = lambda user: user.is_authenticated
else:
    is_authenticated = lambda user: user.is_authenticated()


class OAuth2AccessError(Exception):
    pass

class AuthenticatedUserRequired(OAuth2AccessError):
    pass

class NoTokenFound(OAuth2AccessError):
    pass


class Session(OAuth2Session):
    def __init__(self, service, user=None, **kwargs):
        self.service = service

        # Load config
        try:
            self.conf = settings.OAUTH2ACCESS[service].copy()
        except (AttributeError, KeyError):
            raise ImproperlyConfigured("No settings.OAUTH2ACCESS entry for %s" % service)
        self._fill_kwargs(kwargs, ['client_id', 'scope', 'auto_refresh_url', 'auto_refresh_kwargs'])

        # Set up auto refresh
        if kwargs['auto_refresh_url'] and user and is_authenticated(user):
            kwargs['token_updater'] = lambda token: save_token(service, user, token)

        super(Session, self).__init__(**kwargs)

    def authorization_url(self, state=None, **kwargs):
        """A version of authorization_url that uses config."""
        return super(Session, self).authorization_url(self.conf['auth_url'], state=state, **kwargs)

    def fetch_token(self, **kwargs):
        """A version of fetch_token that uses config."""
        self._fill_kwargs(kwargs, ['client_secret'])
        return super(Session, self).fetch_token(self.conf['token_url'], **kwargs)

    def refresh_token(self, token_url, **kwargs):
        """A version of refresh_token that uses config."""
        self._fill_kwargs(kwargs, ['client_id', 'client_secret'])
        return super(Session, self).refresh_token(token_url, **kwargs)

    def _fill_kwargs(self, kwargs, names):
        for name in names:
            if name in self.conf:
                kwargs.setdefault(name, self.conf[name])


def session(service, user):
    if user is None or not is_authenticated(user):
        raise AuthenticatedUserRequired("User required to get access")

    try:
        service_token = ServiceToken.objects.get(service=service, user=user)
    except ServiceToken.DoesNotExist:
        raise NoTokenFound("No token found to access %s API for given user" % service)

    return Session(service, token=service_token.token, user=user)


def save_token(service, user, token):
    ServiceToken.objects.update_or_create(service=service, user=user,
                                          defaults={'token': token})
