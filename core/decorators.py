from django.contrib import messages
from django.shortcuts import redirect
from funcy import decorator


@decorator
def block_POST_for_incompetent(call):  # noqa
    request = call.request
    if request.method != 'POST' or request.user.is_competent or request.user.is_superuser:
        return call()

    messages.error(
        request,
        'You need to <a href="/competence/">confirm your competence</a> before making any changes.'
    )
    return redirect(request.get_full_path())
