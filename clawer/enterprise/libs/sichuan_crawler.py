#!/usr/bin/env python
#encoding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import requests
import re
import os, os.path
import time
import json
import logging
import datetime
from bs4 import BeautifulSoup
from enterprise.libs.CaptchaRecognition import CaptchaRecognition
import random
import threading

from common_func import get_proxy, exe_time, get_user_agent
import gevent
from gevent import Greenlet
import gevent.monkey
import traceback

headers = {
    'Connetion': 'Keep-Alive',
    'Accept': 'text/html, application/xhtml+xml, */*',
    'Accept-Language': 'en-US, en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
    "User-Agent": get_user_agent()
}


class SichuanCrawler(object):
    """ 四川爬虫， 继承object， 验证码与陕西一致。"""
    write_file_mutex = threading.Lock()

    def __init__(self, json_restore_path=None):
        self.pripid = None
        self.cur_time = str(int(time.time() * 1000))
        self.reqst = requests.Session()
        self.reqst.headers.update(headers)
        adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.reqst.mount('http://', adapter)
        self.json_restore_path = json_restore_path
        self.ckcode_image_path = self.json_restore_path + '/sichuan/ckcode.jpg'
        #html数据的存储路径
        self.html_restore_path = self.json_restore_path + '/sichuan/'
        self.code_cracker = CaptchaRecognition('sichuan')
        self.result_json_dict = {}
        self.json_list = []

        proxies = get_proxy('shaanxi')
        if proxies:
            print proxies
            self.reqst.proxies = proxies
        self.timeout = (30, 20)
        self.ents = {}

        self.mydict = {
            'eareName': 'http://www.ahcredit.gov.cn',
            'search': 'http://gsxt.scaic.gov.cn/ztxy.do?method=index&random=',
            'searchList':
            'http://gsxt.scaic.gov.cn/ztxy.do?method=list&djjg=&random=',
            'validateCode': 'http://gsxt.scaic.gov.cn/ztxy.do?method=createYzm'
        }

        self.one_dict = {u'基本信息': 'ind_comm_pub_reg_basic',
                         u'股东信息': 'ind_comm_pub_reg_shareholder',
                         u'发起人信息': 'ind_comm_pub_reg_shareholder',
                         u'股东（发起人）信息': 'ind_comm_pub_reg_shareholder',
                         u'变更信息': 'ind_comm_pub_reg_modify',
                         u'主要人员信息': 'ind_comm_pub_arch_key_persons',
                         u'分支机构信息': 'ind_comm_pub_arch_branch',
                         u'清算信息': 'ind_comm_pub_arch_liquidation',
                         u'动产抵押登记信息': 'ind_comm_pub_movable_property_reg',
                         u'股权出置登记信息': 'ind_comm_pub_equity_ownership_reg',
                         u'股权出质登记信息': 'ind_comm_pub_equity_ownership_reg',
                         u'行政处罚信息': 'ind_comm_pub_administration_sanction',
                         u'经营异常信息': 'ind_comm_pub_business_exception',
                         u'严重违法信息': 'ind_comm_pub_serious_violate_law',
                         u'抽查检查信息': 'ind_comm_pub_spot_check'}

        self.two_dict = {
            u'企业年报': 'ent_pub_ent_annual_report',
            u'企业投资人出资比例': 'ent_pub_shareholder_capital_contribution',
            u'股东（发起人）及出资信息': 'ent_pub_shareholder_capital_contribution',
            u'股东及出资信息（币种与注册资本一致）': 'ent_pub_shareholder_capital_contribution',
            u'股东及出资信息': 'ent_pub_shareholder_capital_contribution',
            u'股权变更信息': 'ent_pub_equity_change',
            u'行政许可信息': 'ent_pub_administration_license',
            u'知识产权出资登记': 'ent_pub_knowledge_property',
            u'知识产权出质登记信息': 'ent_pub_knowledge_property',
            u'行政处罚信息': 'ent_pub_administration_sanction',
            u'变更信息': 'ent_pub_shareholder_modify'
        }
        self.three_dict = {u'行政许可信息': 'other_dept_pub_administration_license',
                           u'行政处罚信息': 'other_dept_pub_administration_sanction'}
        self.four_dict = {u'股权冻结信息': 'judical_assist_pub_equity_freeze',
                          u'司法股权冻结信息': 'judical_assist_pub_equity_freeze',
                          u'股东变更信息': 'judical_assist_pub_shareholder_modify',
                          u'司法股东变更登记信息':
                          'judical_assist_pub_shareholder_modify'}

    def get_check_num(self):
        # print self.mydict['search']+self.cur_time
        resp = self.reqst.get(self.mydict['search'] + self.cur_time, timeout=self.timeout)
        if resp.status_code != 200:
            # print resp.status_code
            return None
        # print BeautifulSoup(resp.content).prettify
        resp = self.reqst.get(self.mydict['validateCode'] + '&dt=%s&random=%s' % (self.cur_time, self.cur_time),
                              timeout=self.timeout)
        if resp.status_code != 200:
            # print 'no validateCode'
            return None
        with open(self.ckcode_image_path, 'wb') as f:
            f.write(resp.content)

        ck_code = self.code_cracker.predict_result(self.ckcode_image_path)
        if ck_code is None:
            return None
        else:
            return ck_code[1]

    def analyze_showInfo(self, page):
        soup = BeautifulSoup(page, 'html.parser')
        divs = soup.find_all('div',
                             attrs={
                                 "style":
                                 "width:950px; padding:25px 20px 0px; overflow: hidden;float: left;"
                             })
        if divs:
            try:
                Ent = {}
                count = 0
                for div in divs:
                    count += 1
                    link = div.find('li')
                    url = ""
                    if link and link.find('a') and link.find('a').has_attr('onclick'):
                        url = link.find('a')['onclick']
                    ent = ""
                    profile = link.find_next_sibling()
                    if profile and profile.span:
                        ent = profile.span.get_text().strip()
                    name = link.find('a').get_text().strip()
                    if self.ent_num == name or self.ent_num == ent:
                        Ent.clear()
                        Ent[ent] = url
                        break
                    if count == 3:
                        break
                if not Ent:
                    return False
                self.ents = Ent
                return True

            except:
                logging.error(u"%s" % (traceback.format_exc(10)))
        return False

    def get_id_num(self, findCode):
        count = 0
        while count < 20:
            yzm = self.get_check_num()
            print yzm
            count += 1
            if yzm is None:
                continue

            data = {'currentPageNo': '1', 'yzm': yzm, 'cxym': "cxlist", 'maent.entname': findCode}
            resp = self.reqst.post(self.mydict['searchList'] + self.cur_time, data=data, timeout=self.timeout)
            if self.analyze_showInfo(resp.content):
                return True
            print "crawl %s times:%d" % (findCode, count)
            time.sleep(random.uniform(1, 4))
        return False

    def help_dcdy_get_dict(self, method, maent_pripid, maent_xh, random):
        data = {'method': method, 'maent.pripid': maent_pripid, 'maent.xh': maent_xh, 'random': random}
        resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
        needdict = {}
        for table in BeautifulSoup(resp.content, 'html.parser').find_all('table'):
            dcdy_head, dcdy_allths, dcdy_alltds = self.get_head_ths_tds(table)
            needdict[dcdy_head] = self.get_one_to_one_dict(dcdy_allths, dcdy_alltds)
        return needdict

    def help_enter_get_dict(self, method, maent_pripid, year, random):
        data = {'method': method, 'maent.pripid': maent_pripid, 'maent.nd': year, 'random': random}
        resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
        #print resp.status_code
        #print BeautifulSoup(resp.content).prettify
        needdict = {}
        for i, table in enumerate(BeautifulSoup(resp.content, 'html.parser').find_all('table')):
            enter_head, enter_allths, enter_alltds = self.get_head_ths_tds(table)
            if i == 0:
                try:
                    enter_head = enter_allths[0]
                    enter_allths = enter_allths[1:]
                except:
                    enter_head = u'企业基本信息'
                    enter_allths = [u'注册号/统一社会信用代码', u'企业名称', u'企业联系电话', u'邮政编码', \
                        u'企业通信地址', u'企业电子邮箱', u'有限责任公司本年度是否发生股东股权转让', u'企业经营状态', \
                        u'是否有网站或网店', u'是否有投资信息或购买其他公司股权', u'从业人数']
            if enter_head == u'股东及出资信息':
                enter_allths = [u'股东', u'认缴出资额（万元）', u'认缴出资时间', u'认缴出资方式', u'实缴出资额（万元）', u'出资时间', u'出资方式']
            #self.test_print_all_ths_tds(enter_head, enter_allths, enter_alltds)
            needdict[enter_head] = self.get_one_to_one_dict(enter_allths, enter_alltds)
            if enter_head == u'企业基本信息' or enter_head == u'企业资产状况信息':
                needdict[enter_head] = self.get_one_to_one_dict(enter_allths, enter_alltds)[0]
        return needdict

    def help_detail_get_dict(self, method, maent_xh, maent_pripid, random):
        data = {'method': method, 'maent.xh': maent_xh, 'maent.pripid': maent_pripid, 'random': random}
        resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
        # print resp.status_code
        # print BeautifulSoup(resp.content).prettify
        for table in BeautifulSoup(resp.content, 'html.parser').find_all('table'):
            if table.find_all('th') and table.find_all('th')[0].get_text().strip() == u'股东及出资信息':
                #print table
                detail_head, detail_allths, detail_alltds = self.get_head_ths_tds(table)
                # self.test_print_all_ths_tds(detail_head, detail_allths, detail_alltds)
                tempdict = {}
                for key, value in zip(detail_allths[:3], detail_alltds[:3]):
                    tempdict[key] = value
                onelist_dict = {}
                for key, value in zip(detail_allths[3:], detail_alltds[3:]):
                    onelist_dict[key] = value.split('\n')[-1] if value else None
                tempdict['list'] = [onelist_dict]
                return {u'股东及出资信息': [tempdict]}
                break

    def get_head_ths_tds(self, table):
        # print table
        try:
            head = table.find_all('th')[0].get_text().strip().split('\n')[0].strip()
        except:
            head = None
            pass
        allths = [th.get_text().strip() for th in table.find_all('th')[1:] if th.get_text()]
        for i, th in enumerate(allths):
            if th[:2] == '<<' or th[-2:] == '>>':
                allths = allths[:i]
                break
        alltds = [td.get_text().strip() if td.get_text() else None for td in table.find_all('td')]
        if head == u'变更信息' or head == u'修改记录' or head == u'行政处罚信息':
            alltds = []
            for td in table.find_all('td'):
                if td.get_text():
                    if len(td.find_all('span')) > 1:
                        alltds.append(td.find_all('span')[1].get_text().strip().split('\n')[0].strip())
                    else:
                        alltds.append(td.get_text().strip())
                else:
                    alltds.append(None)

        if head == u'主要人员信息':
            allths = allths[:int(len(allths) / 2)]
        if head == u'股东及出资信息':
            allths = allths[:3] + allths[5:]
        if head == u'股东信息':
            alltds = []
            for td in table.find_all('td'):
                if td.find('a'):
                    onclick = td.a['onclick']
                    m = re.search(r"showRyxx\(\'(\w+?)\',\'(\w+?)\'\)", onclick)
                    if m:
                        maent_xh = m.group(1)
                        maent_pripid = m.group(2)
                        #print 'maent_xh',':', maent_xh,'maent_pripid',':',maent_pripid
                        #print self.help_detail_get_dict('tzrCzxxDetial',maent_xh, maent_pripid, self.cur_time)
                        alltds.append(self.help_detail_get_dict('tzrCzxxDetial', maent_xh, maent_pripid, self.cur_time))
                elif td.get_text():
                    alltds.append(td.get_text().strip())
                else:
                    alltds.append(None)
        if head == u'企业年报':
            alltds = []
            for td in table.find_all('td'):
                if td.find('a'):
                    onclick = td.a['onclick']
                    m = re.search(r'doNdbg\(\'(\w+)\'\)', onclick)
                    if m:
                        alltds.append(td.get_text().strip())
                        alltds.append(self.help_enter_get_dict('ndbgDetail', self.pripid, m.group(1), self.cur_time))
                elif td.get_text():
                    alltds.append(td.get_text().strip())
                else:
                    alltds.append(None)
            allths.insert(2, u'详情')
        if head == u'动产抵押登记信息':
            alltds = []
            for td in table.find_all('td'):
                if td.find('a'):
                    onclick = td.a['onclick']
                    m = re.search(r'doDcdyDetail\(\'(\w+?)\'\)', onclick)
                    if m:
                        alltds.append(self.help_dcdy_get_dict('dcdyDetail', self.pripid, m.group(1), self.cur_time))
                elif td.get_text():
                    alltds.append(td.get_text().strip())
                else:
                    alltds.append(None)
        # if len(alltds) == 0:
        # 	alltds = [None for th in allths]
        return head, allths, alltds

    def get_one_to_one_dict(self, allths, alltds):
        if len(allths) == len(alltds):
            one_to_one_dict = {}
            for key, value in zip(allths, alltds):
                one_to_one_dict[key] = value
            return [one_to_one_dict]
        else:
            templist = []
            x = 0
            y = x + len(allths)
            while y <= len(alltds):
                tempdict = {}
                for keys, values in zip(allths, alltds[x:y]):
                    tempdict[keys] = values
                x = y
                y = x + len(allths)
                templist.append(tempdict)
            return templist

    def test_print_table(self, tables):
        for table in tables:
            print table

    def test_print_all_ths_tds(self, head, allths, alltds):
        print '--------------', head, '--------------'
        for th in allths:
            print th
        for td in alltds:
            print td

    def test_print_all_dict(self, mydict):
        for key, value in mydict.items():
            print key, ':', value

    def get_table_by_head(self, tables, head_item):
        for table in tables:
            if table.find_all('th'):
                temp_head = table.find_all('th')[0].get_text().strip().split('\n')[0].strip()
                #print 'temp_head', temp_head, 'head_item', head_item
                if temp_head == head_item:
                    return table
        # else:
        # 	print 'no'*10
        pass

    def get_json_one(self, mydict, tables, *param):
        #self.test_print_table(tables)
        for head_item in param:
            #print '----'*10, head_item
            table = self.get_table_by_head(tables, head_item)
            if table:
                head, allths, alltds = self.get_head_ths_tds(table)
                #self.test_print_all_ths_tds(head, allths, alltds)
                self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)
        pass

    def get_json_two(self, mydict, tables):
        #self.test_print_table(tables)
        for head_item in param:
            #print '----'*10, head_item
            table = self.get_table_by_head(tables, head_item)
            if table:
                head, allths, alltds = self.get_head_ths_tds(table)
                #self.test_print_all_ths_tds(head, allths, alltds)
                self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)

        pass

    def get_json_three(self, mydict, tables):
        #self.test_print_table(tables)
        for head_item in param:
            #print '----'*10, head_item
            table = self.get_table_by_head(tables, head_item)
            if table:
                head, allths, alltds = self.get_head_ths_tds(table)
                #self.test_print_all_ths_tds(head, allths, alltds)
                self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)

        pass

    def get_json_four(self, mydict, tables):
        #self.test_print_table(tables)
        for head_item in param:
            #print '----'*10, head_item
            table = self.get_table_by_head(tables, head_item)
            if table:
                head, allths, alltds = self.get_head_ths_tds(table)
                #self.test_print_all_ths_tds(head, allths, alltds)
                self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)
        pass

    def main_page(self):
        gevent.monkey.patch_socket()
        sub_json_list = []
        for ent, url in self.ents.items():
            m = re.search(r"openView\(\'(\w+?)\'", url)
            if m:
                self.pripid = m.group(1)
            self.result_json_dict = {}
            print self.pripid

            def qyInfo():
                data = {'method': 'qyInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk1', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'), u'基本信息',
                                  u'股东信息', u'变更信息')

            def baInfo():
                data = {'method': 'baInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk2', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'主要人员信息', u'分支机构信息', u'清算信息')

            def dcdyInfo():
                data = {'method': 'dcdyInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk4', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'动产抵押登记信息')

            def gqczxxInfo():
                data = {'method': 'gqczxxInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk4', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'股权出质登记信息')

            def jyycInfo():
                data = {'method': 'jyycInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk6', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'经营异常信息')

            def yzwfInfo():
                data = {'method': 'yzwfInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk14', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'严重违法信息')

            def cfInfo():
                data = {'method': 'cfInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk3', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'行政处罚信息')

            def ccjcInfo():
                data = {'method': 'ccjcInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk7', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.one_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'抽查检查信息')

            def qygsInfo():
                data = {'method': 'qygsInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk8', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.two_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'), u'企业年报')

            def qygsForTzrxxInfo():
                data = {'method': 'qygsForTzrxxInfo',
                        'maent.pripid': self.pripid,
                        'czmk': 'czmk12',
                        'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.two_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'股东及出资信息', u'变更信息')

            def cqygsForTzrbgxxInfo():
                data = {'method': 'cqygsForTzrbgxxInfo',
                        'maent.pripid': self.pripid,
                        'czmk': 'czmk15',
                        'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.two_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'股权变更信息')

            def qygsForXzxkInfo():
                data = {'method': 'qygsForXzxkInfo',
                        'maent.pripid': self.pripid,
                        'czmk': 'czmk10',
                        'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.two_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'行政许可信息')

            def qygsForZzcqInfo():
                data = {'method': 'qygsForZzcqInfo',
                        'maent.pripid': self.pripid,
                        'czmk': 'czmk11',
                        'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.two_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'知识产权出质登记信息')

            def qygsForXzcfInfo():
                data = {'method': 'qygsForXzcfInfo',
                        'maent.pripid': self.pripid,
                        'czmk': 'czmk13',
                        'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.two_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'行政处罚信息')

            def qtgsInfo():
                data = {'method': 'qtgsInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk9', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.three_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'行政许可信息')

            def qtgsForCfInfo():
                data = {'method': 'qtgsForCfInfo',
                        'maent.pripid': self.pripid,
                        'czmk': 'czmk16',
                        'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.three_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'行政处罚信息')

            def sfgsInfo():
                data = {'method': 'sfgsInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk17', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.four_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'司法股权冻结信息')

            def sfgsbgInfo():
                data = {'method': 'sfgsbgInfo', 'maent.pripid': self.pripid, 'czmk': 'czmk18', 'random': self.cur_time}
                resp = self.reqst.post('http://gsxt.scaic.gov.cn/ztxy.do', data=data, timeout=self.timeout)
                self.get_json_one(self.four_dict, BeautifulSoup(resp.content, 'html.parser').find_all('table'),
                                  u'司法股东变更登记信息')

            threads = []
            threads.append(gevent.spawn(qyInfo))
            threads.append(gevent.spawn(baInfo))
            threads.append(gevent.spawn(dcdyInfo))
            threads.append(gevent.spawn(gqczxxInfo))
            threads.append(gevent.spawn(jyycInfo))
            threads.append(gevent.spawn(yzwfInfo))
            threads.append(gevent.spawn(cfInfo))
            threads.append(gevent.spawn(ccjcInfo))
            threads.append(gevent.spawn(qygsInfo))
            threads.append(gevent.spawn(qygsForTzrxxInfo))
            threads.append(gevent.spawn(cqygsForTzrbgxxInfo))
            threads.append(gevent.spawn(qygsForXzxkInfo))
            threads.append(gevent.spawn(qygsForZzcqInfo))
            threads.append(gevent.spawn(qygsForXzcfInfo))
            threads.append(gevent.spawn(qtgsInfo))
            threads.append(gevent.spawn(qtgsForCfInfo))
            threads.append(gevent.spawn(sfgsInfo))
            threads.append(gevent.spawn(sfgsbgInfo))

            gevent.joinall(threads)
            self.result_json_dict['ind_comm_pub_reg_basic'] = self.result_json_dict['ind_comm_pub_reg_basic'][0]
            if 'ind_comm_pub_arch_liquidation' in self.result_json_dict.keys() and len(self.result_json_dict[
                    'ind_comm_pub_arch_liquidation']) > 0:
                self.result_json_dict['ind_comm_pub_arch_liquidation'] = self.result_json_dict[
                    'ind_comm_pub_arch_liquidation'][0]
            sub_json_list.append({ent: self.result_json_dict})
        return sub_json_list

    def run(self, findCode):
        print self.__class__.__name__
        logging.error('crawl %s .', self.__class__.__name__)
        self.ent_num = str(findCode)
        if not os.path.exists(self.html_restore_path):
            os.makedirs(self.html_restore_path)

        if not self.get_id_num(self.ent_num):
            return json.dumps([{self.ent_num: None}])

        data = self.main_page()
        return json.dumps(data)
