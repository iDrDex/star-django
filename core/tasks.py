import json

from celery import shared_task
from handy.db import fetch_all

from .conf import redis_client


# TODO: debounce this task
@shared_task
def update_graph():
    total_graph_sql = """
        SELECT date_trunc('day', S.created_on),
               sum(count(*)) over (order by date_trunc('day', S.created_on))
        FROM raw_sample_annotation A
        JOIN raw_series_annotation S on (A.series_annotation_id = S.id)
        WHERE S.is_active
        GROUP BY 1 ORDER BY 1
    """
    agreed_graph_sql = """
        SELECT date_trunc('day', S.created_on),
               sum(count(*)) over (order by date_trunc('day', S.created_on))
        FROM raw_sample_annotation A
        JOIN raw_series_annotation S on (A.series_annotation_id = S.id)
        WHERE S.is_active and (S.agrees_with_id is not null or S.agreed)
        GROUP BY 1 ORDER BY 1
    """
    disagreed_graph_sql = """
        SELECT date_trunc('day', S.created_on),
               sum(count(*)) over (order by date_trunc('day', S.created_on))
        FROM raw_sample_annotation A
        JOIN raw_series_annotation S on (A.series_annotation_id = S.id)
        WHERE S.is_active and S.agrees_with_id is null and not S.agreed
            and (S.canonical_id not in (select annotation_id from validation_job)
                or S.id = (select min(id) from raw_series_annotation
                           where canonical_id = S.canonical_id))
        GROUP BY 1 ORDER BY 1
    """

    total = fetch_all(total_graph_sql)
    right = fetch_all(agreed_graph_sql)
    wrong = fetch_all(disagreed_graph_sql)
    graph_data = {'total': total, 'right': right, 'wrong': wrong}
    redis_client.set('core.graph', json.dumps(graph_data, default=defaultencode))


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
