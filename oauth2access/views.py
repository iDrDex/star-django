from functools import wraps

from django.http import HttpResponseForbidden, HttpResponseRedirect
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .session import Session, session, save_token, NoTokenFound


def require(service):
    def decorator(func):

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                oauth = session(service, request.user)
            except NoTokenFound:
                # TODO: make https
                redirect_uri = request.build_absolute_uri(reverse('oauth2callback'))
                oauth = Session(service, redirect_uri=redirect_uri)
                authorization_url, state = oauth.authorization_url()
                request.session['oauth2access'] = [service, state, request.build_absolute_uri()]
                return HttpResponseRedirect(authorization_url)

            return func(request, *args, **kwargs)

        return wrapper
    return decorator


def callback(request):
    try:
        code = request.GET['code']
        state = request.GET['state']
        service, saved_state, next_url = request.session['oauth2access']
        if state != saved_state:
            return ValueError
    except (KeyError, ValueError):
        return HttpResponseForbidden("Failing callback: possible CSRF attack.")

    redirect_uri = request.build_absolute_uri(reverse('oauth2callback'))
    oauth = Session(service, redirect_uri=redirect_uri)
    token = oauth.fetch_token(code=code)
    save_token(service, request.user, token)
    request.session.pop('oauth2access', None)  # Clear session
    return HttpResponseRedirect(next_url)
