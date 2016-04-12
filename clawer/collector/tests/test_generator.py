#encoding=utf-8
import json
import os
import datetime
import logging

# from django.test.client import Client
# from django.core.urlresolvers import reverse
# from django.contrib.auth.models import User as DjangoUser, Group

# from clawer.management.commands import task_generator_run, task_analysis, task_analysis_merge, task_dispatch
# from clawer.utils import UrlCache, Download, MonitorClawerHour
# from clawer.utils import DownloadClawerTask

from django.test import TestCase
from django.conf import settings
from collector.models import CrawlerTask, CrawlerTaskGenerator, CrawlerGeneratorErrorLog, CrawlerGeneratorAlertLog, GrawlerGeneratorCronLog
from mongoengine import *

class TestMongodb(TestCase):
    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost', alias='testdb')
        conn = get_connection('testdb')

    def tearDown(self):
        TestCase.tearDown(self)

    def test_job(self):
        job = Job(name='job')
        job.save()
        count = Job.objects(name='job').count()
        self.assertEqual(count, 1)


"""
class TestHomeApi(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.user = DjangoUser.objects.create_user(username="xxx", password="xxx")
        self.group = Group.objects.create(name=MenuPermission.GROUPS[0])
        self.user.groups.add(self.group)
        self.client = Client()
        self.logined_client = Client()
        self.logined_client.login(username=self.user.username, password=self.user.username)
        self.url_cache = UrlCache()

    def tearDown(self):
        TestCase.tearDown(self)
        self.user.delete()
        self.group.delete()

    def test_all(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        url = reverse("clawer.apis.home.clawer_all")

        resp = self.logined_client.get(url)
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()

    def test_clawer_add(self):
        url = reverse("clawer.apis.home.clawer_add")
        data = {'name': 'hello', 'info': 'Good word', 'customer': 'daddd'}
        resp = self.logined_client.post(url, data)
        self.assertEqual(resp.status_code, 200)

        result = json.loads(resp.content)
        self.assertEqual(result["is_ok"], True)

    def test_download_log(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        clawer_generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print hello", cron="*", status=ClawerTaskGenerator.STATUS_PRODUCT)
        clawer_task = ClawerTask.objects.create(clawer=clawer, task_generator=clawer_generator, uri="http://github.com", status=ClawerTask.STATUS_FAIL)
        download_log = ClawerDownloadLog.objects.create(clawer=clawer, task=clawer_task)
        url = reverse("clawer.apis.home.clawer_download_log")

        resp = self.logined_client.get(url)
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        clawer_generator.delete()
        clawer_task.delete()
        download_log.delete()

    def test_task(self):
        self.url_cache.flush()
        clawer = Clawer.objects.create(name="hi", info="good")
        clawer_generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print hello", cron="*", status=ClawerTaskGenerator.STATUS_PRODUCT)
        clawer_task = ClawerTask.objects.create(clawer=clawer, task_generator=clawer_generator, uri="http://github.com", status=ClawerTask.STATUS_FAIL)
        url = reverse("clawer.apis.home.clawer_task")

        resp = self.logined_client.get(url)
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        clawer_generator.delete()
        clawer_task.delete()

    def test_task_analysis_failed_reset(self):
        self.url_cache.flush()
        clawer = Clawer.objects.create(name="hi", info="good")
        clawer_generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print hello", cron="*", status=ClawerTaskGenerator.STATUS_PRODUCT)
        clawer_task = ClawerTask.objects.create(clawer=clawer, task_generator=clawer_generator, uri="http://github.com", status=ClawerTask.STATUS_ANALYSIS_FAIL)
        url = reverse("clawer.apis.home.clawer_task_reset")

        resp = self.logined_client.get(url, {"clawer": clawer.id, "status":ClawerTask.STATUS_ANALYSIS_FAIL})
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        clawer_generator.delete()
        clawer_task.delete()

    def test_task_process_reset(self):
        self.url_cache.flush()
        clawer = Clawer.objects.create(name="hi", info="good")
        clawer_generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print hello", cron="*", status=ClawerTaskGenerator.STATUS_PRODUCT)
        clawer_task = ClawerTask.objects.create(clawer=clawer, task_generator=clawer_generator, uri="http://github.com", status=ClawerTask.STATUS_PROCESS)
        url = reverse("clawer.apis.home.clawer_task_reset")

        resp = self.logined_client.get(url, {"clawer": clawer.id, "status":ClawerTask.STATUS_PROCESS})
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        clawer_generator.delete()
        clawer_task.delete()

    def test_task_add(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        url = reverse("clawer.apis.home.clawer_task_add")

        resp = self.logined_client.post(url, {"clawer":clawer.id, "uri":"http://www.1.com"})
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()

    def test_clawer_task_generator_update(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        code_path = "/tmp/test.py"
        code_file = open(code_path, "arw")
        code_file.write("print 'http://www.github.com'\n")
        code_file.close()
        code_file = open(code_path)
        url = reverse("clawer.apis.home.clawer_task_generator_update")

        resp = self.logined_client.post(url, data={"code_file":code_file, "clawer":clawer.id, "cron":"*"})
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        task_generator = ClawerTaskGenerator.objects.get(clawer=clawer)
        self.assertGreater(len(task_generator.code), 0)

        clawer.delete()
        task_generator.delete()
        os.remove(code_path)

    def test_clawer_task_generator_history(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        clawer_generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print hello", cron="*", status=ClawerTaskGenerator.STATUS_PRODUCT)
        url = reverse("clawer.apis.home.clawer_task_generator_history")

        resp = self.logined_client.get(url)
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        clawer_generator.delete()

    def test_clawer_analysis_update(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        code_path = "/tmp/test.py"
        code_file = open(code_path, "arw")
        code_file.write("print 'http://www.github.com'\n")
        code_file.close()
        code_file = open(code_path)
        url = reverse("clawer.apis.home.clawer_analysis_update")

        resp = self.logined_client.post(url, data={"code_file":code_file, "clawer":clawer.id})
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        analysis = ClawerAnalysis.objects.get(clawer=clawer)
        self.assertGreater(len(analysis.code), 0)

        clawer.delete()
        analysis.delete()
        os.remove(code_path)

    def test_clawer_analysis_history(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        analysis = ClawerAnalysis.objects.create(clawer=clawer, code="print")
        url = reverse("clawer.apis.home.clawer_analysis_history")

        resp = self.logined_client.get(url, {"clawer_id":clawer.id})
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        analysis.delete()

    def test_clawer_analysis_log(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        analysis = ClawerAnalysis.objects.create(clawer=clawer, code="print")
        task_generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="sss", cron="*")
        task = ClawerTask.objects.create(clawer=clawer, task_generator=task_generator, uri="http://www.csdn.net")
        analysis_log = ClawerAnalysisLog.objects.create(clawer=clawer, analysis=analysis, task=task)
        url = reverse("clawer.apis.home.clawer_analysis_log")

        resp = self.logined_client.get(url)
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        analysis.delete()
        analysis_log.delete()

    def test_clawer_generate_log(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        task_generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="sss", cron="*")
        generate_log = ClawerGenerateLog.objects.create(clawer=clawer, task_generator=task_generator)
        url = reverse("clawer.apis.home.clawer_generate_log")

        resp = self.logined_client.get(url)
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer.delete()
        task_generator.delete()
        generate_log.delete()

    def test_clawer_setting_update(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        url = reverse("clawer.apis.home.clawer_setting_update")
        data = {"dispatch":10, "analysis":90, "clawer":clawer.id, "download_engine":Download.ENGINE_REQUESTS, "status":1,
                "prior": ClawerSetting.PRIOR_URGENCY}

        resp = self.logined_client.post(url, data)
        result = json.loads(resp.content)
        self.assertTrue(result["is_ok"])

        clawer_setting = clawer.settings()
        self.assertEqual(clawer_setting.dispatch, data["dispatch"])

        clawer.delete()



class TestCmd(TestCase):
    def setUp(self):
        TestCase.setUp(self)
        self.user = DjangoUser.objects.create_user(username="xxx", password="xxx")
        self.group = Group.objects.create(name=MenuPermission.GROUPS[0])
        self.user.groups.add(self.group)
        self.url_cache = UrlCache()

    def tearDown(self):
        TestCase.tearDown(self)
        self.user.delete()
        self.group.delete()


    def test_task_generator_run(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print '{\"uri\": \"http://www.github.com\"}'\n", cron="*", status=ClawerTaskGenerator.STATUS_ON)
        product_path = generator.product_path()
        if os.path.exists(product_path):
            os.remove(product_path)

        ret = task_generator_run.run(generator.id)
        self.assertTrue(ret)

        clawer.delete()
        generator.delete()

    def test_task_dispatch(self):
        clawer = Clawer.objects.create(name="hi", info="good")
        generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print '{\"uri\": \"http://www.gitsdhub.com\"}'\n", cron="*")
        task = ClawerTask.objects.create(clawer=clawer, task_generator=generator, uri="https://www.ba90idu.com")

        q = task_dispatch.run()
        self.assertEqual(len(q.jobs), 1)

        clawer.delete()
        generator.delete()
        task.delete()

    def test_task_analysis(self):
        self.url_cache.flush()
        path = "/tmp/ana.store"
        tmp_file = open(path, "w")
        tmp_file.write("hi")
        tmp_file.close()
        clawer = Clawer.objects.create(name="hi", info="good")
        generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print '{\"uri\": \"http://www.gith23ub.com\"}'\n", cron="*")
        task = ClawerTask.objects.create(clawer=clawer, task_generator=generator, uri="https://www.ba56idu.com", store=path, status=ClawerTask.STATUS_SUCCESS)
        analysis = ClawerAnalysis.objects.create(clawer=clawer, code="print '{\"url\":\"ssskkk\"}'\n")

        task_analysis.do_run()

        clawer.delete()
        generator.delete()
        task.delete()
        analysis.delete()
        os.remove(path)

    def test_task_analysis_with_exception(self):
        self.url_cache.flush()
        path = "/tmp/ana.store"
        tmp_file = open(path, "w")
        tmp_file.write("hi")
        tmp_file.close()
        clawer = Clawer.objects.create(name="hi", info="good")
        generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print a", cron="*")
        task = ClawerTask.objects.create(clawer=clawer, task_generator=generator, uri="https://www.baweidu.com", store=path, status=ClawerTask.STATUS_SUCCESS)
        analysis = ClawerAnalysis.objects.create(clawer=clawer, code="print a\n")

        task_analysis.do_run()

        clawer.delete()
        generator.delete()
        task.delete()
        analysis.delete()
        os.remove(path)

    def test_task_analysis_with_large(self):
        path = "/tmp/ana.store"
        tmp_file = open(path, "w")
        tmp_file.write("hi")
        tmp_file.close()
        code = "import json\nresult={}\nfor i in range(100000):\n    result[i] = 'test'\nprint json.dumps(result)"
        clawer = Clawer.objects.create(name="hi", info="good")
        generator = ClawerTaskGenerator.objects.create(clawer=clawer, code=code, cron="*")
        task = ClawerTask.objects.create(clawer=clawer, task_generator=generator, uri="https://www.baidu.com", store=path, status=ClawerTask.STATUS_SUCCESS)
        analysis = ClawerAnalysis.objects.create(clawer=clawer, code=code)

        task_analysis.do_run()

        clawer.delete()
        generator.delete()
        task.delete()
        analysis.delete()
        os.remove(path)

    def test_task_analysis_merge(self):
        pre_hour = datetime.datetime.now() - datetime.timedelta(minutes=60)
        clawer = Clawer.objects.create(name="hi", info="good")
        generator = ClawerTaskGenerator.objects.create(clawer=clawer, code="print '{\"uri\": \"http://www.github111.com\"}'\n", cron="*")
        task = ClawerTask.objects.create(clawer=clawer, task_generator=generator, uri="https://www.baid11u.com")
        analysis = ClawerAnalysis.objects.create(clawer=clawer, code="print '{\"url\":\"ssskkk\"}'\n")
        analysis_log = ClawerAnalysisLog.objects.create(clawer=clawer, analysis=analysis, task=task, status=ClawerAnalysisLog.STATUS_SUCCESS,
                                                        result=json.dumps({"hi":"ok"}), add_datetime=pre_hour)

        task_analysis_merge.run()

        clawer.delete()
        generator.delete()
        task.delete()
        analysis.delete()
        analysis_log.delete()

"""