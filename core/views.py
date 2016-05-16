from funcy import zipdict
from handy.decorators import render_to

from .conf import redis_client


@render_to(template='dashboard.j2')
def dashboard(request):
    keys = ('core.stats.tags', 'core.stats.serie_annotations', 'core.stats.sample_annotations',
            'core.graph')
    return {
        'stats': zipdict(keys, redis_client.mget(*keys))
    }
