#!/usr/bin/env python
#encoding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
# sys.path.append('/Users/princetechs3/Documents/pyenv/cr-clawer/clawer')
import requests
import re
import os, os.path
from crawler import CrawlerUtils
from bs4 import BeautifulSoup
import json

# from . import settings
import settings
import random
from smart_proxy.api import Proxy, UseProxy
from enterprise.libs.CaptchaRecognition import CaptchaRecognition
from collector.models import CrawlerDownloadArgs


class YunnanCrawler(object):
    ckcode_image_path = settings.json_restore_path + '/yunnan/ckcode.jpg'

    def __init__(self, json_restore_path):
        self.id = None
        self.reqst = requests.Session()
        self.json_restore_path = json_restore_path
        self.ckcode_image_path = settings.json_restore_path + '/yunnan/ckcode.jpg'
        if not os.path.exists(os.path.dirname(self.ckcode_image_path)):
            os.makedirs(os.path.dirname(self.ckcode_image_path))
        self.result_json_dict = {}
        self.code_cracker = CaptchaRecognition('yunnan')
        self.reqst.headers.update({
            'Accept': 'text/html, application/xhtml+xml, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language':
            'en-US, en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:39.0) Gecko/20100101 Firefox/39.0'
        })

        useproxy = UseProxy()
        is_use_proxy = useproxy.get_province_is_use_proxy(province='guangxi')
        if not is_use_proxy:
            self.proxies = []
        else:
            proxy = Proxy()
            self.proxies = {
                'http': 'http://' + random.choice(proxy.get_proxy(num=5, province='guangxi')),
                'https': 'https://' + random.choice(proxy.get_proxy(num=5, province='guangxi'))
            }
        print 'self.proxies:', self.proxies
        # self.proxies = []

        self.mydict = {
            'eareName': 'http://www.ahcredit.gov.cn',
            'search': 'http://gsxt.ynaic.gov.cn/notice/',
            'searchList':
            'http://gsxt.ynaic.gov.cn/notice/search/ent_info_list',
            'validateCode':
            'http://gsxt.ynaic.gov.cn/notice/captcha?preset=&ra=0.06570781518790503'
        }

        self.one_dict = {u'基本信息': 'ind_comm_pub_reg_basic',
                         u'股东信息': 'ind_comm_pub_reg_shareholder',
                         u'发起人信息': 'ind_comm_pub_reg_shareholder',
                         u'股东（发起人）信息': 'ind_comm_pub_reg_shareholder',
                         u'合伙人信息': 'ind_comm_pub_reg_shareholder',
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
        self.result_json_dict = {}

    def get_check_num(self):
        resp = self.reqst.get(self.mydict['search'], proxies=self.proxies, timeout=120)
        if resp.status_code != 200:
            return None
        first = resp.content.find('session.token":')
        session_token = resp.content[first + 17:first + 53]

        resp = self.reqst.get(self.mydict['validateCode'], proxies=self.proxies, timeout=120)
        if resp.status_code != 200:
            # print 'no validateCode'
            return None
        with open(self.ckcode_image_path, 'wb') as f:
            f.write(resp.content)

        ck_code = self.code_cracker.predict_result(self.ckcode_image_path)
        if ck_code is None:
            return None, None
        else:
            return ck_code[1], session_token

    def get_id_num(self, findCode):
        count = 0
        while count < 20:
            check_num, session_token = self.get_check_num()
            # print check_num
            if check_num is None:
                count += 1
                continue
            data = {'searchType': '1',
                    'captcha': check_num,
                    "session.token": session_token,
                    'condition.keyword': findCode}
            resp = self.reqst.post(self.mydict['searchList'], data=data, proxies=self.proxies, timeout=120)
            if resp.status_code != 200:
                # print resp.status_code
                # print 'error...(get_id_num)'
                count += 1
                continue
            else:
                try:
                    soup = BeautifulSoup(resp.content, 'html.parser').find_all('div', attrs={'class': 'link'})[0]
                    hrefa = soup.find('a', attrs={'target': '_blank'})
                    if hrefa:
                        self.after_crack_checkcode_page = resp.content
                        return True
                        # return hrefa['href'].split('&')[0]
                    else:
                        count += 1
                        continue
                except:
                    return None

    def get_re_list_from_content(self, content):
        m = re.search(r'investor\.invName = \"(.+)\"', content)
        one = unicode(m.group(1), 'utf8') if m else None
        m = re.search(r'invt\.subConAm = \"(.+)\"', content)
        five = unicode(m.group(1), 'utf8') if m else None
        m = re.search(r'invt\.conDate = [\"|\'](.+)[\"|\']', content)
        six = unicode(m.group(1), 'utf8') if m else None
        m = re.search(r'invt\.conForm = [\"|\'](.+)[\"|\']', content)
        four = unicode(m.group(1), 'utf8') if m else None
        m = re.search(r'invtActl\.acConAm = [\"|\'](.+)[\"|\']', content)
        eight = unicode(m.group(1), 'utf8') if m else None
        m = re.search(r'invtActl\.conDate = [\"|\'](.+)[\"|\']', content)
        nigh = unicode(m.group(1), 'utf8') if m else None
        m = re.search(r'invtActl\.conForm = [\"|\'](.+)[\"|\']', content)
        seven = unicode(m.group(1), 'utf8') if m else None
        return [one, five, eight, four, five, six, seven, eight, nigh]
        pass

    def get_tables(self, url):
        resp = self.reqst.get(url, proxies=self.proxies, timeout=120)
        if resp.status_code == 200:
            return BeautifulSoup(resp.content, 'html.parser').find_all('table')
            #return [table for table in tables] #if (table.find_all('th') or table.find_all('a')) ]
    def get_head_ths_tds(self, table):
        head = table.find_all('th')[0].get_text().strip().split('\n')[0].strip()
        allths = [th.get_text().strip() for th in table.find_all('th')[1:] if th.get_text()]
        if head == u'股东信息' or head == u'发起人信息' or head == u'股东（发起人）信息' or head == u'行政许可信息' or head == u'股权出质登记信息':
            tdlist = []
            for td in table.find_all('td'):
                if td.find_all('a'):
                    tddict = {}
                    detail_head, detail_allths, detail_alltds = self.get_head_ths_tds(self.get_tables(td.a['href'])[0])
                    if detail_head == u'股东及出资信息':
                        detail_content = self.reqst.get(td.a['href'], proxies=self.proxies, timeout=120).content
                        detail_alltds = self.get_re_list_from_content(detail_content)
                        # print '---------------------------', len(detail_allths[:3]+detail_allths[5:]), len(detail_alltds)
                        # tddict = self.get_one_to_one_dict(detail_allths[:3]+detail_allths[5:], detail_alltds)
                        detail_allths = detail_allths[:3] + detail_allths[5:]
                        # self.test_print_all_ths_tds(detail_head, detail_allths, detail_alltds)
                        son_need_dict = {}
                        for key, value in zip(detail_allths[3:], detail_alltds[3:]):
                            son_need_dict[key] = value
                        need_dict = {}
                        for key, value in zip(detail_allths[:3], detail_alltds[:3]):
                            need_dict[key] = value
                        need_dict['list'] = [son_need_dict]
                        tdlist.append({detail_head: [need_dict]})

                        # tdlist.append(tddict)
                    else:
                        tddict = self.get_one_to_one_dict(detail_allths, detail_alltds)
                        tdlist.append(tddict)
                elif td.get_text():
                    tdlist.append(td.get_text().strip())
                else:
                    tdlist.append(None)
            return head, allths, tdlist
            pass
        # elif head == u'股东及出资信息（币种与注册资本一致）' or head == u'股东及出资信息':
        # 	pass
        elif head == u'企业年报':
            tdlist = []
            for td in table.find_all('td'):
                if td.find_all('a'):
                    tddict = {}
                    for i, table in enumerate(self.get_tables(td.a['href'])):
                        enter_head, enter_allths, enter_alltds = self.get_head_ths_tds(table)
                        #print enter_head
                        if i == 0:
                            enter_head = enter_allths[0]
                            enter_allths = enter_allths[1:]
                        #self.test_print_all_ths_tds(enter_head, enter_allths, enter_alltds)
                        tddict[enter_head] = self.get_one_to_one_dict(enter_allths, enter_alltds)
                        if enter_head == u'企业基本信息' or enter_head == u'企业资产状况信息':
                            tddict[enter_head] = self.get_one_to_one_dict(enter_allths, enter_alltds)[0]
                    tdlist.append(td.get_text().strip())
                    tdlist.append(tddict)
                elif td.get_text():
                    tdlist.append(td.get_text().strip())
                else:
                    tdlist.append(None)
            allths.insert(2, u'详情')
            # self.test_print_all_ths_tds(head, allths, tdlist)
            return head, allths, tdlist
            pass
        else:
            if table.find_all('td'):
                alltds = [td.get_text().strip() if td.get_text() else None for td in table.find_all('td')]
            else:
                alltds = [None for th in allths]
                # alltds = []
            if head == u'主要人员信息':
                return head, allths[:int(len(allths) / 2)], alltds
            else:
                return head, allths, alltds
        #return (table.find_all('th')[0].get_text().strip().split('\n')[0].strip(), [th.get_text().strip() for th in table.find_all('th')[1:] if th.get_text()], [td.get_text().strip() if td.get_text() else None for td in table.find_all('td')])

    def get_one_to_one_dict(self, allths, alltds):
        if len(allths) == len(alltds):
            if any(alltds):
                one_to_one_dict = {}
                for key, value in zip(allths, alltds):
                    one_to_one_dict[key] = value
                return [one_to_one_dict]
            else:
                return []
        else:
            templist = []
            x = 0
            y = x + len(allths)
            #print '---------------------%d-------------------------------%d' % (len(allth), len(alltd))
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

    def get_json_one(self, mydict, tables):
        #self.test_print_table(tables)
        for table in tables:
            head, allths, alltds = self.get_head_ths_tds(table)
            #print head
            try:
                self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)
            except:
                pass
            if head == u'基本信息':
                self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)[0]
            if head == u'清算信息':
                if allths:
                    self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)
                else:
                    self.result_json_dict[mydict[head]] = []
            #self.test_print_all_ths_tds(head, allths, alltds)
        pass

    def get_json_two(self, mydict, tables):
        #self.test_print_table(tables)
        for table in tables:
            head, allths, alltds = self.get_head_ths_tds(table)
            #print head
            self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)
        pass

    def get_json_three(self, mydict, tables):
        #self.test_print_table(tables)
        for table in tables:
            head, allths, alltds = self.get_head_ths_tds(table)
            #print head
            self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)

        pass

    def get_json_four(self, mydict, tables):
        #self.test_print_table(tables)
        for table in tables:
            head, allths, alltds = self.get_head_ths_tds(table)
            #print head
            self.result_json_dict[mydict[head]] = self.get_one_to_one_dict(allths, alltds)
        pass

    def run(self, findCode):

        self.ent_number = findCode

        id_args = CrawlerDownloadArgs.objects.filter(register_number=self.ent_number).first() \
           or CrawlerDownloadArgs.objects.filter(unifield_number=self.ent_number).first() \
           or CrawlerDownloadArgs.objects.filter(enterprise_name=self.ent_number).first()
        print id_args
        if id_args and id_args.download_args.get('uuid'):
            self.result_json_dict = {}
            self.uuid = id_args.download_args['uuid']

            tableone = self.get_tables(self.uuid + '&tab=01')
            self.get_json_one(self.one_dict, tableone)
            tabletwo = self.get_tables(self.uuid + '&tab=02')
            self.get_json_two(self.two_dict, tabletwo)
            tablethree = self.get_tables(self.uuid + '&tab=03')
            self.get_json_three(self.three_dict, tablethree)
            tablefour = self.get_tables(self.uuid + '&tab=06')
            self.get_json_four(self.four_dict, tablefour)

            CrawlerUtils.json_dump_to_file('yunnan.json', {self.ent_number: self.result_json_dict})
            print json.dumps({self.ent_number: self.result_json_dict})
            return [{self.ent_number: self.result_json_dict}]
        else:
            #创建目录
            html_restore_path = self.json_restore_path + '/yunnan/'
            if not os.path.exists(html_restore_path):
                os.makedirs(html_restore_path)

            self.uuid = self.get_id_num(findCode)
            if self.uuid is None:
                return json.dumps({self.ent_number: {}})
            self.result_json_dict_list = []
            for div in BeautifulSoup(self.after_crack_checkcode_page,
                                     'html.parser').find_all('div', attrs={'class': 'list-item'}):
                hrefa = div.find_all('a', attrs={'target': '_blank'})[0]
                if hrefa:
                    self.uuid = hrefa['href'].split('&')[0]
                    self.enterprise_name = div.find_all('div', attrs={'class': 'link'})[0].get_text().strip()
                    self.ent_number = div.find_all('span')[0].get_text().strip()

                    args =  CrawlerDownloadArgs.objects.filter(register_number=self.ent_number)\
                       or CrawlerDownloadArgs.objects.filter(unifield_number=self.ent_number).first() \
                       or CrawlerDownloadArgs.objects.filter(enterprise_name=self.ent_number).first()
                    if args:
                        args.delete()
                    args = CrawlerDownloadArgs(province='yunnan',
                                               register_number=self.ent_number,
                                               unifield_number=self.ent_number,
                                               enterprise_name=self.enterprise_name,
                                               download_args={'uuid': self.uuid})
                    args.save()
                else:
                    continue
                print self.uuid
                self.result_json_dict = {}

                tableone = self.get_tables(self.uuid + '&tab=01')
                self.get_json_one(self.one_dict, tableone)
                tabletwo = self.get_tables(self.uuid + '&tab=02')
                self.get_json_two(self.two_dict, tabletwo)
                tablethree = self.get_tables(self.uuid + '&tab=03')
                self.get_json_three(self.three_dict, tablethree)
                tablefour = self.get_tables(self.uuid + '&tab=06')
                self.get_json_four(self.four_dict, tablefour)

                CrawlerUtils.json_dump_to_file('yunnan.json', {self.ent_number: self.result_json_dict})
                print json.dumps({self.ent_number: self.result_json_dict})
                self.result_json_dict_list.append({self.ent_number: self.result_json_dict})
            return self.result_json_dict_list


if __name__ == '__main__':
    yunnan = YunnanCrawler('./enterprise_crawler/yunnan.json')
    # yunnan.run('530000000006503')
    yunnan.run(u'美好置业集团股份有限公司')
    # f = open('enterprise_list/yunnan.txt', 'r')
    # for line in f.readlines():
    # 	print line.split(',')[2].strip()
    # 	yunnan.run(str(line.split(',')[2]).strip())
    # f.close()
