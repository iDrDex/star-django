from urllib import urlencode

from funcy import decorator

from django.conf import settings
from django.shortcuts import redirect


@decorator
def login_required(call):
    if not call.request.user_data.get('id'):
        # NOTE: this _next redirect back not quite works,
        #       cause web2py does strange things there.
        args = {'_next': call.request.build_absolute_uri()}
        return redirect(settings.LEGACY_APP_URL + '/default/user/login?' + urlencode(args))
    return call()
