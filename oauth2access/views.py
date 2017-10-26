from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from .session import Session, session, save_token, NoTokenFound, NoUserFound


def require(service, authorize=True):
    def decorator(func):

        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                oauth = session(service, request.user)
            except NoUserFound as e:
                return HttpResponse(str(e), status=401)
            except NoTokenFound as e:
                if not authorize:
                    return HttpResponseForbidden(str(e))

                oauth = Session(service, redirect_uri=get_callback_uri(request))
                authorization_url, state = oauth.authorization_url()
                request.session['oauth2access'] = [service, state, request.build_absolute_uri()]
                return HttpResponseRedirect(authorization_url)

            setattr(request, service, oauth)
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

    oauth = Session(service, redirect_uri=get_callback_uri(request))
    token = oauth.fetch_token(code=code)
    save_token(service, request.user, token)
    request.session.pop('oauth2access', None)  # Clear session
    return HttpResponseRedirect(next_url)


def get_callback_uri(request):
    path = reverse('oauth2callback')
    # Allow http in DEBUG mode
    if settings.DEBUG:
        return request.build_absolute_uri(path)
    else:
        return 'https://%s%s' % (request.get_host(), path)
