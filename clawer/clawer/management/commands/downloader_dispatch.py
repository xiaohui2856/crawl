# coding=utf-8
from django.core.management.base import BaseCommand
from collector.models import Job, CrawlerTask, CrawlerDownloadSetting, CrawlerDispatchAlertLog
from django.conf import settings
from collector.util_downloader import download_clawer_task
import redis
import rq
import datetime
import socket
import sys
import raven

try:
    redis_url = settings.DOWNLOADER_REDIS
except:
    redis_url = None

redis_conn = redis.Redis.from_url(redis_url) if redis_url else redis.Redis()

q_down_super = rq.Queue('down_super', connection=redis_conn)
q_down_low = rq.Queue('down_low', connection=redis_conn)
q_down_mid = rq.Queue('down_mid', connection=redis_conn)
q_down_high = rq.Queue('down_high', connection=redis_conn)


class SentryClient(object):

    def __init__(self):
        self.client = None
        if hasattr(settings, 'RAVEN_CONFIG'):
            self.client = raven.Client(dsn=settings.RAVEN_CONFIG["dsn"])

    def capture(self):
        if not self.client:
            return
        self.client.captureException()


def write_dispatch_success_log(job, reason):
    print reason
    cdal = CrawlerDispatchAlertLog(
        job=job, types=2, reason=reason, hostname=str(socket.gethostname()))
    cdal.content_bytes = sys.getsizeof(cdal)
    cdal.save()
    pass


def write_dispatch_failed_log(job, reason):
    print reason
    cdal = CrawlerDispatchAlertLog(
        job=job, types=3, reason=reason, hostname=str(socket.gethostname()))
    cdal.content_bytes = sys.getsizeof(cdal)
    cdal.save()
    pass


def write_dispatch_error_log(job, reason):
    print reason
    cdal = CrawlerDispatchAlertLog(
        job=job, types=3, reason=reason, hostname=str(socket.gethostname()))
    cdal.content_bytes = sys.getsizeof(cdal)
    cdal.save()
    pass


def write_dispatch_alter_log(job, reason):
    print reason
    cdal = CrawlerDispatchAlertLog(
        job=job, types=1, reason=reason, hostname=str(socket.gethostname()))
    cdal.content_bytes = sys.getsizeof(cdal)
    cdal.save()
    pass


def dispatch_use_pool(task):
    try:
        # dispatch_num = CrawlerDownloadSetting.objects(job=task.job)[0].dispatch_num
        dispatch_num = 1
        if dispatch_num == 0:
            write_dispatch_alter_log(job=task.job, reason='dispatch_num is 0')
            return
        # print type(dispatch_num), dispatch_num
        max_retry_times = CrawlerDownloadSetting.objects(job=task.job)[
            0].max_retry_times
        if settings.OPEN_CRAWLER_FAILED_ONLY:
            down_tasks = CrawlerTask.objects(
                status=CrawlerTask.STATUS_FAIL).order_by('?')[:dispatch_num]
        else:
            if datetime.datetime.now().minute >= 56:
                # max_retry_times <= max_retry_times
                down_tasks = CrawlerTask.objects(
                    status=CrawlerTask.STATUS_FAIL, retry_times__lte=max_retry_times).order_by('?')[:dispatch_num]
            else:
                down_tasks = CrawlerTask.objects(
                    status=CrawlerTask.STATUS_LIVE).order_by('?')[:dispatch_num]
            if len(down_tasks) == 0:
                # write_dispatch_alter_log(job=task.job, reason='get down_tasks len is 0')
                return
    except Exception as e:
        write_dispatch_error_log(job=task.job, reason=str(e))
        return None

    for task in down_tasks:
        priority = task.job.priority
        try:
            task.status = CrawlerTask.STATUS_DISPATCH
            if priority == -1:
                if len(q_down_super) >= settings.Q_DOWN_SUPER_LEN:
                    write_dispatch_alter_log(
                        job=task.job, reason='q_down_super lens get maxlen')
                    continue
                q_down_super.enqueue(download_clawer_task, args=[task], timeout=settings.RQ_DOWNLOAD_TASK_TIMEOUT)
            elif priority == 0:
                if len(q_down_high) >= settings.Q_DOWN_HIGH_LEN:
                    write_dispatch_alter_log(
                        job=task.job, reason='q_down_high lens get maxlen')
                    continue
                q_down_high.enqueue(download_clawer_task,
                                    args=[task], at_front=True, timeout=settings.RQ_DOWNLOAD_TASK_TIMEOUT)
            elif priority == 1:
                if len(q_down_high) >= settings.Q_DOWN_HIGH_LEN:
                    write_dispatch_alter_log(
                        job=task.job, reason='q_down_high lens get maxlen')
                    continue
                q_down_high.enqueue(download_clawer_task, args=[
                                    task], at_front=False, timeout=settings.RQ_DOWNLOAD_TASK_TIMEOUT)
            elif priority == 2:
                if len(q_down_mid) >= settings.Q_DOWN_MID_LEN:
                    write_dispatch_alter_log(
                        job=task.job, reason='q_down_mid lens get maxlen')
                    continue
                q_down_mid.enqueue(download_clawer_task,
                                   args=[task], at_front=True, timeout=settings.RQ_DOWNLOAD_TASK_TIMEOUT)
            elif priority == 3:
                if len(q_down_mid) >= settings.Q_DOWN_MID_LEN:
                    write_dispatch_alter_log(
                        job=task.job, reason='q_down_mid lens get maxlen')
                    continue
                q_down_mid.enqueue(download_clawer_task, args=[
                                   task], at_front=False, timeout=settings.RQ_DOWNLOAD_TASK_TIMEOUT)
            elif priority == 4:
                if len(q_down_low) >= settings.Q_DOWN_LOW_LEN:
                    write_dispatch_alter_log(
                        job=task.job, reason='q_down_low lens get maxlen')
                    continue
                q_down_low.enqueue(download_clawer_task,
                                   args=[task], at_front=True, timeout=settings.RQ_DOWNLOAD_TASK_TIMEOUT)
            elif priority == 5:
                if len(q_down_low) >= settings.Q_DOWN_LOW_LEN:
                    write_dispatch_alter_log(
                        job=task.job, reason='q_down_low lens get maxlen')
                    continue
                q_down_low.enqueue(download_clawer_task, args=[
                                   task], at_front=False, timeout=settings.RQ_DOWNLOAD_TASK_TIMEOUT)

            task.save()
            write_dispatch_success_log(job=task.job, reason='success')
        except Exception as e:
            task.status = CrawlerTask.STATUS_FAIL
            write_dispatch_failed_log(job=task.job, reason=str(e))


def run():
    print 'Downloader dispatch start'
    if settings.DISPATCH_BY_PRIORITY:
        total = 0
        jobs = Job.objects(status=Job.STATUS_ON).order_by('+priority')
        print "All jobs Number:", jobs.count()
        for job in jobs:
            total = CrawlerTask.objects(job=job).count()
            print 'This job\'s tasks total number:', total

            dispatch_tasks_num = settings.MAX_TOTAL_DISPATCH_COUNT_ONCE                # 测试每次分发的数量
            tasks = CrawlerTask.objects(job=job, status=1)[:dispatch_tasks_num]
            print "Tasks Count:", len(tasks)
            if len(tasks) > dispatch_tasks_num:
                print "Downloader dispatch Error: Tasks number over MAX_TOTAL_DISPATCH_COUNT_ONCE：", dispatch_tasks_num
                break

            count = 0
            for task in tasks:
                print "Downloader task dispatch :", count
                count += 1
                dispatch_use_pool(task)
            # pool.map(dispatch_use_pool, tasks)
            # pool.close()
            # pool.join()
        # tasks = CrawlerTask.objects(status=CrawlerTask.STATUS_LIVE).order_by('job.priority')[:settings.MAX_TOTAL_DISPATCH_COUNT_ONCE]
    elif settings.DISPATCH_BY_HOSTNAME:
        # TODO:按照主机进行分发
        pass


def empty_all():
    pass


class Command(BaseCommand):
    # @wrapper_raven
    def handle(self, *args, **options):
        run()
