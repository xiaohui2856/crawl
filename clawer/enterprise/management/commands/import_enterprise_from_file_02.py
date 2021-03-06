# coding=utf-8
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from django.utils.encoding import smart_unicode

from html5helper.utils import wrapper_raven

from collector.utils_generator import CrawlerCronTab
from enterprise.models import Enterprise, Province
from uri_filter.api.api_uri_filter import bloom_filter_api
import time
import os
import traceback
import codecs
import logging

level = logging.debug
logging.basicConfig(level=level, format="%(levelname)s %(asctime)s %(lineno)d:: %(message)s")


class Command(BaseCommand):

    help = " This command is used to import enterprises from file."

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('filename', nargs='?', help='enterprise filename')
        # Named (optional) arguments
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            default=False,
                            help='Delete poll instead of closing it')
        pass

    # @wrapper_raven
    def handle(self, *args, **options):
        # print options
        if options['delete']:
            self.delete_all()
            return
        filename = options['filename']
        if not os.path.exists(filename):
            print "The file %s doesn't exist!" % (filename)
            return
        start_time = time.time()
        print self.add(filename)
        # print self.read(filename)
        end_time = time.time()
        print "Run time is %f s!" % (end_time - start_time)

    def delete_all(self):
        count = Enterprise.objects.all().delete()
        print "delete all enterprises! %s" % (count)

    def read(self, filename):
        success = 0
        failed = 0
        multiple = 0
        line_count = 0
        with codecs.open(filename, 'r', 'GB18030') as f:
            f.readline()
            while True:
                try:
                    _line = f.readline()
                except Exception:
                    failed += 1
                    continue
                if not _line:
                    break
                if success > 40:
                    break
                success += 1
                # print _line
                line_count += 1
                line = _line.strip().split(";")[0]
                fields = line.strip().split(",")
                if len(fields) < 3:
                    failed += 1
                    continue

                name = smart_unicode(fields[0])
                province = self.auto_fix_name(smart_unicode(fields[1]))
                province_id = Province.to_id(province)
                register_no = fields[2]

                print "name:%s ; province_id:%d; register_no: %s !" % (name, province_id, register_no)
                if not province_id:
                    failed += 1
                    continue
                if not register_no:
                    register_no = "***"

                # if Enterprise.objects.filter(name=name).count() > 0:
                #     multiple += 1
                #     continue
                # elif Enterprise.objects.filter(register_no=register_no).count() > 0:
                #     multiple += 1
                #     continue

                Enterprise.objects.create(name=name, province=province_id, register_no=register_no)
        return {"is_ok": True, 'success': success, 'failed': failed}

    def add(self, filename):
        try:
            with codecs.open(filename, 'r+', 'GB18030') as f:
                success = 0
                failed = 0
                multiple = 0
                line_count = 0

                f.readline()
                enterprises = []
                slice = 0
                while True:
                    _line = f.readline()
                    if not _line:
                        break
                    #if success >8000:
                    #   break
                    line_count += 1
                    line = _line.strip().split(";")[0]
                    fields = line.strip().split(",")
                    if len(fields) < 3:
                        failed += 1
                        continue

                    name = smart_unicode(fields[0])
                    province = self.auto_fix_name(smart_unicode(fields[1]))
                    province_id = Province.to_id(province)
                    register_no = fields[2]

                    if not province_id:
                        failed += 1
                        continue
                    if not register_no:
                        register_no = "***"

                    # if Enterprise.objects.filter(name=name).count() > 0:
                    #     multiple += 1
                    #     continue
                    # elif Enterprise.objects.filter(register_no=register_no).count() > 0:
                    #     multiple += 1
                    #     continue

                    # if not bloom_filter_api("uri_generator", [name]) :
                    #     multiple += 1
                    #     continue
                    enterprises.append([name, province_id, register_no])
                    # enterprises.append(Enterprise(name=name, province=province_id, register_no=register_no))
                    success += 1
                    if success % 1000 == 0:    # 每1000个存一次
                        if success % 10000 == 0:    # 每10000个分片一次
                            slice += 1
                        de_ents = bloom_filter_api("uri_generator", enterprises)
                        multiple += len(enterprises) - len(de_ents)
                        ent_list = []
                        for ent in de_ents:
                            ent_list.append(Enterprise(name=ent[0], province=ent[1], register_no=ent[2], slice=slice))
                        Enterprise.objects.bulk_create(ent_list)
                        enterprises = []
                        print "success_count = %d." % (success)
                # Enterprise.objects.bulk_create(enterprises)

                return {"is_ok": True,
                        "line_count": line_count,
                        'success': success,
                        'slice': slice,
                        'failed': failed,
                        'multiple': multiple}
        except Exception, e:
            print traceback.format_exc(10)
            print "Exception occured %s!" % (type(e))

    def auto_fix_name(self, province):
        if province == u"黑龙":
            return u"黑龙江"
        elif province == u"内蒙":
            return u"内蒙古"
        return province
