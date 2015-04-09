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


@shared_task
def update_graph():
    SAMPLES_GRAPH_SQL = """
        SELECT d, sum(c) over (order by d) FROM
        (
            SELECT date_trunc('day', created_on), count(*) FROM sample_tag group by 1
            UNION
            SELECT date_trunc('day', created_on), count(*) FROM sample_validation group by 1
            UNION
            SELECT date_trunc('day', created_on), count(*) FROM sample_validation__backup group by 1
        ) as foo (d, c)
        order by 1
    """
    WRONG_VALIDATIONS_GRAPH_SQL = """
        SELECT date_trunc('day', V.created_on),
               sum(count(*)) over (order by date_trunc('day', V.created_on))
            FROM sample_validation V
            JOIN series_validation SV on (V.serie_validation_id = SV.id)
            JOIN series_tag ST on (SV.series_tag_id = ST.id)
            JOIN sample_tag T on (V.sample_id = T.sample_id and T.series_tag_id = ST.id)
        WHERE V.annotation != T.annotation
        GROUP BY 1 ORDER BY 1
    """


    total = fetch_all(SAMPLES_GRAPH_SQL, server='legacy')
    wrong = fetch_all(WRONG_VALIDATIONS_GRAPH_SQL, server='legacy')
    graph_data = {'total': total, 'wrong': wrong}
    redis_client.set('core.graph', json.dumps(graph_data, default=defaultencode))


# Utils

from datetime import datetime
from decimal import Decimal
import pytz


EPOCH = datetime.fromtimestamp(0).replace(tzinfo=pytz.timezone('UTC'))


def unix_milliseconds(dt):
    return int((dt - EPOCH).total_seconds() * 1000)

def defaultencode(obj):
    if isinstance(obj, datetime):
        return unix_milliseconds(obj)
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError("%r is not JSON serializable" % obj)
