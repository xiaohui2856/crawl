# coding=utf-8
#!/usr/bin/python
from django.core.management.base import BaseCommand
from structure.structure import ParserGenerator, Consts
from django.conf import settings
import redis
import rq


def run():
    q = None
    queue_name = raw_input()
    try:
        redis_url = settings.STRUCTURE_REDIS
    except:
        redis_url = None
    connection = redis.Redis.from_url(redis_url)
    too_high_queue = rq.Queue(Consts.QUEUE_PRIORITY_TOO_HIGH, connection=connection)
    high_queue = rq.Queue(Consts.QUEUE_PRIORITY_HIGH, connection=connection)
    normal_queue = rq.Queue(Consts.QUEUE_PRIORITY_NORMAL, connection=connection)
    low_queue = rq.Queue(Consts.QUEUE_PRIORITY_LOW, connection=connection)
    if queue_name == "structure:higher":
        q = too_high_queue
    elif queue_name == "structure:high":
        q = high_queue
    elif queue_name == "structure:normal":
        q = normal_queue
    elif queue_name == "structure:low":
        q = low_queue
    else:
        print "Error: Cannot find the queue from Redis."
    if q is not None:
        with rq.Connection(connection):
            w = rq.Worker([q])
            w.work()


class Command(BaseCommand):
    args = ""
    help = "Dispatch Parser Task"

    #@wrapper_raven
    def handle(self, *args, **options):
        run()
