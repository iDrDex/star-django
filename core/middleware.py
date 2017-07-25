from django.contrib.auth.decorators import login_required


class LoginRequired:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/accounts/') or request.path.startswith('/admin/'):
            return None
        return login_required(view_func)(request, *view_args, **view_kwargs)
