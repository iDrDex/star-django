from optparse import make_option

from funcy import project
from django.core.management.base import BaseCommand, CommandError

from analysis.analysis import task_analyze


class Command(BaseCommand):
    args = 'analysis_name'
    help = 'Make new analysis'

    option_list = BaseCommand.option_list + (
        make_option(
            '--desc',
            action='store', type='string', dest='description', default='',
            help='Analysis description'
        ),
        make_option(
            '--case',
            action='store', type='string', dest='case_query',
            help='Case query (required)'
        ),
        make_option(
            '--control',
            action='store', type='string', dest='control_query',
            help='Control query (required)'
        ),
        make_option(
            '--modifier',
            action='store', type='string', dest='modifier_query', default='',
            help='Modifier query'
        ),
        make_option(
            '--debug',
            action='store_true', dest='debug', default=False,
        ),
    )

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Specify analysis name')
        analysis_name = args[0]
        fields = ['description', 'case_query', 'control_query', 'modifier_query', 'debug']
        task_analyze(analysis_name, **project(options, fields))
