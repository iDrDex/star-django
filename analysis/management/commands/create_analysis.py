from funcy import project
from django.core.management.base import BaseCommand

from legacy.models import Analysis
from analysis.tasks import analysis_task


class Command(BaseCommand):
    args = 'analysis_name'
    help = 'Make new analysis'

    def add_arguments(self, parser):
        parser.add_argument('analysis_name', help='Analysis name')
        parser.add_argument('--desc', dest='description', default='', help='Analysis description')
        parser.add_argument('--specie', default='', help='Specie')

        # Conditions
        parser.add_argument('--case', dest='case_query', default='', required=True,
                            help='Case query')
        parser.add_argument('--control', dest='control_query', default='', required=True,
                            help='Control query')
        parser.add_argument('--modifier', dest='modifier_query', default='',
                            help='Modifier query')

    def handle(self, *args, **options):
        fields = ['analysis_name', 'description', 'specie',
                  'case_query', 'control_query', 'modifier_query']
        analysis = Analysis.objects.create(**project(options, fields))
        analysis_task(analysis.pk)
