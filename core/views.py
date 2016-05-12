from funcy import zipdict
from handy.decorators import render_to
from registration.backends.hmac.views import RegistrationView

from .conf import redis_client
from .forms import MyRegistrationForm


@render_to(template='dashboard.j2')
def dashboard(request):
    keys = ('core.stats.tags', 'core.stats.serie_annotations', 'core.stats.sample_annotations',
            'core.graph')
    return {
        'stats': zipdict(keys, redis_client.mget(*keys))
    }


class MyRegistrationView(RegistrationView):
    form_class = MyRegistrationForm
