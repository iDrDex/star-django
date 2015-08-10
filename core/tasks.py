import json

from celery import shared_task
from handy.db import fetch_val, fetch_all

from .conf import redis_client


@shared_task
def update_stats():
    tags = fetch_val('select count(*) from tag', server='legacy')
    redis_client.set('core.stats.tags', tags)

    serie_annotations = fetch_val(
        '''select (select count(*) from series_tag)
                + (select count(*) from series_validation)''',
        server='legacy')
    redis_client.set('core.stats.serie_annotations', serie_annotations)

    sample_annotations = fetch_val(
        '''select (select count(*) from sample_tag)
                + (select count(*) from sample_validation)
                + (select count(*) from sample_validation__backup)''',
        server='legacy')
    redis_client.set('core.stats.sample_annotations', sample_annotations)


# TODO: debounce this task
@shared_task
def update_graph():
    samples_graph_sql = """
        SELECT date_trunc('day', created_on),
               sum(count(*)) over (order by date_trunc('day', created_on))
        FROM sample_tag GROUP BY 1 ORDER BY 1
    """
    # TODO: update this to use concordant field
    validations_graph_sql = """
        SELECT date_trunc('day', V.created_on),
               sum(count(*)) over (order by date_trunc('day', V.created_on))
            FROM sample_validation V
            JOIN series_validation SV on (V.serie_validation_id = SV.id)
            JOIN series_tag ST on (SV.series_tag_id = ST.id)
            JOIN sample_tag T on (V.sample_id = T.sample_id and T.series_tag_id = ST.id)
        WHERE V.annotation %s T.annotation
        GROUP BY 1 ORDER BY 1
    """

    total = fetch_all(samples_graph_sql, server='legacy')
    right = fetch_all(validations_graph_sql % '=', server='legacy')
    wrong = fetch_all(validations_graph_sql % '!=', server='legacy')
    graph_data = {'total': total, 'right': right, 'wrong': wrong}
    redis_client.set('core.graph', json.dumps(graph_data, default=defaultencode))


from celery import group

update_dashboard = group(update_stats.si(), update_graph.si())


# Utils

from datetime import datetime
from decimal import Decimal
import pytz


EPOCH_NAIVE = datetime.fromtimestamp(0)
EPOCH = EPOCH_NAIVE.replace(tzinfo=pytz.timezone('UTC'))

def unix_milliseconds(dt):
    epoch = EPOCH_NAIVE if dt.tzinfo is None else EPOCH
    return int((dt - epoch).total_seconds() * 1000)

def defaultencode(obj):
    if isinstance(obj, datetime):
        return unix_milliseconds(obj)
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError("%r is not JSON serializable" % obj)
