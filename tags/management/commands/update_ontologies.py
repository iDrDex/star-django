from django.core.management.base import BaseCommand
from core.conf import redis_client
from django.conf import settings
import pickle
import requests

class Command(BaseCommand):
    help = 'Update ontologies list'

    def handle(self, *args, **kwargs):
        response = requests.get(
            'http://data.bioontology.org/ontologies',
            headers={
                'Authorization': 'apikey token={0}'.format(
                    settings.BIOPORTAL_API_KEY
                )
            })
        if response.status_code == 200:
            data = [(ontology['acronym'], ontology['name'])
                    for ontology in response.json()]
            redis_client.set('ontologies', pickle.dumps(data), 1000 * 60 * 60 * 24)
