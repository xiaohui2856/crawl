# coding=utf-8
from django.core.management.base import BaseCommand
from html5helper.utils import wrapper_raven
from structure.structure import ParserGenerator, ExecutionTasks

def run():
    	parsergenerator = ParserGenerator()
    	parser_task_queues = parsergenerator.assign_parse_tasks()
    	return parser_task_queues
    
class Command(BaseCommand):
    	args = ""
    	help = "Dispatch Parser Task"
    	
    	#@wrapper_raven
    	def handle(self, *args, **options):
    		run()