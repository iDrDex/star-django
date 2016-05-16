from django.contrib import messages
from django.shortcuts import redirect
from funcy import decorator


@decorator
def block_POST_for_incompetent(call):  # noqa
    if call.request.method != 'POST' or call.request.user.is_competent:
        return call()

    messages.error(call.request, 'You need to confirm your competence before making any changes')
    return redirect(call.request.get_full_path())
