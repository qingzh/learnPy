# -*- coding:utf8 -*-

"""
参数：
server: 服务器地址
method: http method
urllink: api目标链接
headers: http headers
body: http body

主要功能：
1. 添加计划: addCampaign
2. 更新计划: updateCampaign
3. 根据id获取计划: getCampaignByCampaignId
4. 获取所有计划: getAllCampaign
5. 获取所有计划id: getAllCampaignID
6. ：/getProductAdsCampaignID

"""

import json
import yaml
import requests
import regex
from requests import Request, Session, utils
import logging
import os
import re
import sys
from datetime import datetime, date
import time
from APITest.model.models import (
    zipORtar, RequestHeader, BulkJobBody, APIRequest, APIData)
from APITest.utils import (
    SafeConfigParser, sub_commas, md5_of_file, assert_object)
from APITest.model.models import log_stdout, json_dump_decorator
import threading
from multiprocessing import Pool
import xlrd
import csv
from APITest.model.models import sample, AttributeDict
from APITest.utils import write_file
from APITest.settings import BLOCK_SIZE, SERVER, USERS, api
import itertools
from APITest.model.bulkJob import bulkJobRequestType

####################################################
#   set response.json to AttributeDict
####################################################


def decorator_response(func):
    def wrapper(*args, **kwargs):
        kwargs['object_hook'] = AttributeDict
        return func(*args, **kwargs)
    return wrapper

requests.models.Response.json = decorator_response(
    requests.models.Response.json)

####################################################
#   add `"bulkJobRequestType"` in json
####################################################


def prepare(obj):
    if isinstance(obj.json.body, bulkJobRequestType):
        obj.json.body = {'bulkJobRequestType': obj.json.body}
    return super(type(obj), obj).prepare()

APIRequest.prepare = prepare

####################################################
#   for debug
####################################################

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_stdout.setLevel(logging.DEBUG)
log.addHandler(log_stdout)

__variable__ = None

###################################################
#   main
###################################################

CASE_PREFIX = 'CASE'

shenma = USERS.get('ShenmaPM2.5')
xiecheng = USERS.get(u'携程旅行网')
DEFAULT_USER = USERS.get('uc-ganji-wapzf1')
ZIP_DIRECTORY = 'E:/API_BULK'


body_cases = [
    (None, None, None, None, None),  # Body = null
    ([], 0, 0, [], 0),  # Default value
    ([], 0, 1, [], 0),  # gzip
]
bulkBody = bulkJobRequestType()

CASE_XIECHENG = [
    ([20262562], 0, 0, None, 0b1111110110),  # 关键词 332098
    ([20262562], 0, 0, None, 0b1111101110),  # 创意 332098
]
keyword_filter = []

# 测试多文件模式的，单个文件；通过
body_single_cases_gz = [
    ([], 0, 1, None, 1020),
    ([], 0, 1, None, 1018),
    ([], 0, 1, None, 1014),
    ([], 0, 1, None, 1006),
    ([], 0, 1, None, 990),
    ([], 0, 1, None, 958),
    ([], 0, 1, None, 894),
    ([], 0, 1, None, 766),
    ([], 0, 1, None, 510)
]

multi_single_cases = [
    (None, None, None, None, None),  # Body = null
    (None, 1, None, None, None),  # Default value
]

body = APIData(header=DEFAULT_USER)


def get_taskid_by_json(params=None, server=SERVER, user=DEFAULT_USER):
    '''
    post data
    get taskId
    '''
    body = APIData(header=user, body=params)
    req = api.bulkJob.getAllObjects(json=body)
    res = req.response(server)
    log.debug('[REQUEST ] %s' % res.request.body)
    log.debug('[RESPONSE] %s' % res.content)
    try:
        bd = res.json()
        assert bd.body.status == 'CREATED'
        return bd.body.taskId
    except ValueError as e:
        _for_debug(res)
        raise
    return bd.header.desc


def _for_debug(x):
    global __variable__
    __variable__ = x


def get_fileid_by_taskid(taskid, server=SERVER, user=DEFAULT_USER):
    '''
    post taskId
    get taskState and fileId
    '''
    log.debug('[THREAD] [%s] is running...', threading.current_thread().name)
    data = APIData(header=user, body=dict(taskId=taskid))
    req = api.task.getTaskState(json=data)

    while True:
        res = req.response(server)
        log.debug('[REQUEST ] %s' % res.request.body)
        log.debug('[RESPONSE] %s' % res.content)
        try:
            body = res.json().body
            assert body.taskId == taskid, '%s != %s' % (body.taskId, taskid)
            if body.status != 'FINISHED':
                time.sleep(3)
            else:
                return body.get('fileId')
        except ValueError as e:
            _for_debug(res)
            pass
        except AssertionError as e:
            print res.url
            print res.request.body
            _for_debug(res)
            raise
    return res


def get_file_by_fileid(fileid, filename, server=SERVER, user=DEFAULT_USER, check=True):
    '''
    download file by fileId
    '''
    log.info('Download FileID [%s] to [%s]' % (fileid, filename))
    data = APIData(header=user, body=dict(fileId=fileid))
    req = api.file.download(json=data)
    res = req.response(server, stream=True)
    write_file(res.iter_content(BLOCK_SIZE), filename)
    archive_check_md5(filename)
    return filename


def _get_file_by_taskid(taskid, server=SERVER, user=DEFAULT_USER):
    fileid = get_fileid_by_taskid(taskid, server, user)
    filename = ZIP_DIRECTORY + '/%s_%s_%s' % (user.username, taskid, fileid)
    return get_file_by_fileid(fileid, filename, server, user)


def _get_file_by_json(params=None, server=SERVER, user=DEFAULT_USER):
    taskid = get_taskid_by_json(params, server, user)
    return _get_file_by_taskid(taskid, server, user)


def get_file_by_taskids(ids, server=SERVER, user=DEFAULT_USER):
    '''
    """
    something odd using multi thread
    """
    def func_dec(func, obj):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            obj.append(result)
        return wrapper

    name_list = []
    func = func_dec(_get_file_by_taskid, name_list)
    func_thread = lambda x: threading.Thread(
        target=func, name='<TASK %s>' % x, args=(x, server, user))
    threads = map(func_thread, ids)
    # map(lambda x: x.setDaemon(True), threads)
    map(lambda x: x.start(), threads)
    map(lambda x: x.join(), threads)
    return name_list
    '''
    return map(lambda x: _get_file_by_taskid(x, server, user), ids)


def get_file_by_cases(tc_list, server=SERVER, user=DEFAULT_USER):
    task_list = map(lambda x: get_taskid_by_json(x, server, user), tc_list)
    name_list = get_file_by_taskids(task_list, server, user)
    return task_list, name_list


def get_md5_from_file(filename, mode='r'):
    with zipORtar.open(filename, mode) as z:
        md5_list = filter(lambda x: x.endswith('.md5'), z.getnames())
        return map(lambda x: z.extractfile(x).read(), md5_list)


def check_man_one(multi, single):
    '''
    multi zip archive files where variableColumns in
        (~0b10, ~0b100 ... ~0b100000000) & 0b1111111111
    vs
    single zip archive files where variableColumns = 0b0
    '''
    print multi, single
    with zipORtar.open(multi, 'r') as m, zipORtar.open(single, 'r') as s:
        s_file = s.extractfile(s.getnames()[0])
        s_file.readline()
        name_list = filter(lambda x: x.endswith('.csv'), m.getnames())
        log.debug('single: %s\nmulti:\n%s', single, str(name_list))
        for name in name_list:
            m_file = m.extractfile(name)
            header = m_file.readline()  # ignore the table header
            for line in m_file:
                s_line = sub_commas(s_file.readline())
                if s_line != line:
                    msg = 'Content differ:\n%s\n%s: %s\n%s: %s' % (
                        header, name.encode('utf-8'), line, s.getnames()[0].encode('utf-8'), s_line)
                    log.warning(msg)
                    raise Exception(msg)
            else:
                log.info('[SAME] %s', name)
    return True


def check_one_one(name_a, name_b):
    with zipORtar.open(name_a, 'r') as A, zipORtar.open(name_b, 'r') as B:
        Alist = filter(
            lambda x: x.endswith('.csv') and not x.startswith('App'), A.getnames())
        Blist = filter(
            lambda x: x.endswith('.csv') and not x.startswith('App'), B.getnames())
        for namea, nameb in itertools.izip(Alist, Blist):
            Afile = A.extractfile(namea)
            Bfile = B.extractfile(nameb)
            for linea, lineb in itertools.izip(Afile.readlines(), Bfile.readlines()):
                if linea.strip() != lineb.strip():
                    log.warning('Content differ:\n%s, %s: \n%s\n%s, %s: \n%s' % (
                        name_a.encode('utf-8'), namea.encode('utf-8'), linea, name_b.encode('utf-8'), nameb.encode('utf-8'), lineb))
                    return False
            log.debug('[SUCC] %s | %s' % (
                namea.encode('utf-8'), nameb.encode('utf-8')))
    return True

idea_filter = ['campaignName', 'adgroupName', 'title',
               'description', 'destinationUrl', 'displayUrl']
keyword_filter = ['campaignName', 'adgroupName',
                  'keyword', 'matchType', 'price', 'destinationUrl']
match_types = [i.encode('utf-8') for i in [u'精确', u'短语', u'广泛']]


def check_csv_xls(csvname, xlsname, csv_filter):
    book = xlrd.open_workbook(xlsname)
    sheet = book.sheets()[0]
    csv_list = []
    with open(csvname, 'r') as f:
        g = csv.reader(f)
        header = g.next()
        csv_idx = map(lambda x: header.index(x), csv_filter)
        try:
            while True:
                line = g.next()
                csv_list.append([line[i] if header[i] != 'matchType' else match_types[
                                int(line[i])] for i in csv_idx])
        except StopIteration as e:
            pass
    if len(csv_list) != sheet.nrows - 1:
        raise Exception('length of two files dismatched: %d,%d' %
                        (len(csv_list), sheet.nrows - 1))

    func = lambda x: x.encode(
        'utf-8') if isinstance(x, unicode) else str(x)
    data = sorted((map(func, sheet.row_values(i))
                   for i in xrange(1, sheet.nrows)))
    csv_list = sorted(csv_list)

    for idx in xrange(sheet.nrows - 1):
        for i, value in enumerate(data[idx]):
            if value != str(csv_list[idx][i]):
                print idx, i
                print 'xls:', value
                print 'csv:', csv_list[idx][i]
                return sheet.row(idx + 1), csv_list[idx]
                raise Exception(u'[ERROR] not the same value')
    return True


def archive_check_md5(filename, mode='r'):
    log.info('[CHECK] %s' % filename)
    with zipORtar.open(filename, mode) as z:
        # check MD5 in *.md5 match the md5 of the file content
        csv_list = filter(lambda x: x.endswith('.csv'), z.getnames())
        md5_list = filter(lambda x: x.endswith('.md5'), z.getnames())
        for idx, csv_name in enumerate(csv_list):
            md5_name = md5_list[idx]
            '''
            # check pair of CSV and MD5 filename
            if md5_name[: -8] != csv_name[: -8]:
                raise Exception(
                    'csv and md5 files not matched:\n%s\n%s' % (csv_name.encode('utf-8'), md5_name.encode('utf-8')))
            '''
            ret_md5 = z.extractfile(md5_name).read()  # tarFile
            ext_md5 = md5_of_file(z.extractfile(csv_name)).hexdigest()
            if ext_md5 != ret_md5:
                raise Exception('md5 of file not matched:\n%s\nExpected MD5: %s\nExact MD5: %s\n' % (
                    csv_name.encode('utf-8'), ret_md5, ext_md5))
    return True


def test_md5_same(file_list):
    '''
    @params file_list: list of filenames
    @return md5_list: list of md5 of each file
    '''
    md5_list = map(lambda x: get_md5_from_file(x), file_list)
    ret = reduce(lambda x, y: y if x == y else False, md5_list)
    log.info('[MD5] %s' % (True if ret else False))
    return md5_list, True if ret else False


def datetime_to_str(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()


class AuthRequest(Request):
    reg = regex.compile('code=(?P<code>[^&]+)')
    token_pair = [('-1', '-1')]
    code = ['-1']

    def __init__(self, **kwargs):
        self.server = kwargs.get('server', '42.120.172.21')
        self.scope = kwargs.get('scope', '')
        self.redirect_uri = kwargs.get('redirect_uri', '')
        self.username = kwargs.get('username', 'ShenmaPM2.5')
        self.grant_type = kwargs.get('grant_type', 'refreshtoken')
        self.password = 'pd123456'
        self.client_id = kwargs.get('client_id', '')
        self.client_secret = kwargs.get('client_secret', 'pd123456')
        self.response_type = kwargs.get('response_type', 'code')
        self.state = kwargs.get('state', 'test')
        self.token = 'd789a6c8-e6d9-4d7c-bf16-0f518d6888b1'

    def get_params(self):
        return dict(
            server=self.server,
            scope=self.scope,
            redirect_uri=self.redirect_uri,
            username=self.username,
            grant_type=self.grant_type,
            password=self.password,
            client_id=self.client_id,
            client_secret=self.client_secret,
            response_type=self.response_type,
            state=self.state,
            token=self.token,
            code=self.code[-1],
            refresh_token=self.token_pair[-1][0],
            access_token=self.token_pair[-1][1],
        )

    def get_authorized(self, allow_redirects=False, **kwargs):
        params = self.get_params()
        params.update(kwargs)
        authorize_url = 'http://{server}/auth/authorization/authorizationRequest?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}'.format(
            **params)
        res = requests.get(authorize_url, allow_redirects=allow_redirects)
        print res.headers
        if 'location' in res.headers:
            self.code.append(self.reg.search(
                res.headers.get('location')).group('code'))
        return res

    def get_confirmed(self, allow_redirects=False, **kwargs):
        params = self.get_params()
        params.update(kwargs)
        authorize_url = 'http://{server}/auth/authorization/confirmAuthorization?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={state}&username={username}&password={password}'.format(
            **params)
        res = requests.post(authorize_url, allow_redirects=allow_redirects)
        print res.headers
        if 'location' in res.headers:
            self.code.append(self.reg.search(
                res.headers.get('location')).group('code'))
        return res

    def get_token(self, **kwargs):
        params = self.get_params()
        params['grant_type'] = 'authorization_code'
        params.update(kwargs)
        access_token_url = 'http://{server}/auth/authorization/accessTokenRequest?grant_type={grant_type}&code={code}&client_secret={client_secret}&client_id={client_id}&redirect_uri={redirect_uri}'.format(
            **params)
        res = requests.post(access_token_url, allow_redirects=False)
        try:
            res_dict = res.json()
            print res_dict
            if 'refresh_token' in res_dict:
                self.token_pair.append((
                    res_dict.get('refresh_token', ''),
                    res_dict.get('access_token', ''),
                    res_dict.get('scope'),
                ))
        except Exception as e:
            pass
        return res

    def do_auth(self, auth_type=1, target_url='', **kwargs):
        params = self.get_params()
        params.update(dict(
            username=self.username if auth_type == 0 else self.client_id,
            access_token=self.token if auth_type == 0 else self.token_pair[
                -1][1],
            type=auth_type,
            target_url=target_url))
        params.update(kwargs)
        auth_url = 'http://{server}/auth/mock/authenticate?type={type}&username={username}&password={password}&token={access_token}&targetUrl={target_url}&targetId='.format(
            **params)
        res = requests.post(auth_url)
        print res.text
        return res

    def do_refresh(self, **kwargs):
        params = self.get_params()
        params.update(kwargs)
        refresh_url = 'http://{server}/auth/authorization/accessTokenRefresh?grant_type={grant_type}&refresh_token={refresh_token}&scope={scope}'.format(
            **params)
        res = requests.post(refresh_url)
        try:
            res_dict = res.json()
            print res_dict
            if 'refresh_token' in res_dict:
                self.token_pair.append((
                    res_dict.get('refresh_token', ''),
                    res_dict.get('access_token', ''),
                    res_dict.get('scope'),
                ))
        except Exception as e:
            pass
        return res


def test_access_token(server=SERVER, client_id=2, client_secret='pd123456', redirect_uri='http://baidu.com'):
    reg = regex.compile('code=(?P<code>[^&]+)')
    authorize_url = 'http://{server}/auth/authorization/confirmAuthorization?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=2&state=test&username=shenmaPM2.5&password=pd123456'.format(
        server=server, client_id=client_id, redirect_uri=redirect_uri)
    access_url = 'http://{server}/auth/authorization/accessTokenRequest?grant_type=authorization_code&code=%s&client_secret={client_secret}&client_id={client_id}&redirect_uri={redirect_uri}'.format(
        server=server, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    res = requests.post(authorize_url, allow_redirects=False)
    print res.headers
    code = reg.search(res.headers.get('location')).group('code')
    res = requests.post(access_url % code, allow_redirects=False)
    return res


def getRequestHeader(**kwargs):
    return sample(HEADER_ARGS, kwargs)


def parse_config(file, prefix=CASE_PREFIX):
    '''
    input: config file
    return: dict(key=json, key=json, ...)
    '''
    cf.read(file)
    TEST_RUNNER = 'RUNNER'
    if TEST_RUNNER in cf.sections():
        try:
            cases = cf.get(TEST_RUNNER, 'cases')
            case_list = [i.strip()
                         for i in cases.split(',') if i.strip() in cf.sections()]
        except NoOptionError:
            case_list = cf.sections()
    else:
        case_list = cf.sections()
    for key in case_list:
        if key.upper().startswith(prefix):
            conf_dict = cf._sections[key]
            conf_dict['body'] = str_to_json(cf.get(key, 'body'))
            conf_dict['HTTP_URL'] = cf.get(key, 'http_url')
            conf_dict['HTTP_METHOD'] = cf.get(key, 'http_method')
            conf_dict['HTTP_DATA'] = str_to_json(cf.get(key, 'http_data'))
            conf_dict['HTTP_HEADERS'] = str_to_dict(
                cf.get(key, 'http_headers'))
            conf_dict['assert'] = str_to_dict(cf.get(key, 'assert'))
            yield conf_dict


def str_to_dict(s):
    '''
    input: string
    return: convert string to dict
    '''
    if s is None:
        return None
    if isinstance(s, basestring):
        return yaml.load(s)
    return s


def str_to_json(s):
    '''
    input: string
    return: json object
    '''
    # s = ?? return '{}'
    # diff between null and '{}'
    if s is None or s.strip() is '':
        return 'null'
    if isinstance(s, basestring) is False:
        return s
    return json.dumps(str_to_dict(s), default=datetime_to_str)


class TestCampaign(object):

    server = '42.120.172.21'
    headers = {'Content-Type': 'application/json;charset=UTF-8'}
    extra_body = '"header":{"username":"ShenmaPM2.5","password":"pd123456","token":"d789a6c8-e6d9-4d7c-bf16-0f518d6888b1"}'

    def __init__(self):
        self.campaigns = [
            '{"campaignName":"测试4","budget":40,"regionTarget":["内蒙古"],"excludeIp":["1.3.3.3","1.3.33.0"],"negativeWords":["3232","培训"],"exactNegativeWords":["3232","培训"],"schedule":[{"weekDay":1,"startHour":1,"endHour":5}]}',
            '{"campaignName":"测试3","budget":40,"regionTarget":["内蒙古"],"excludeIp":["1.3.3.3","1.3.33.0"],"negativeWords":["3232","培训"],"exactNegativeWords":["3232","培训"],"schedule":[{"weekDay":1,"startHour":1,"endHour":5}]}',
            '{"campaignName":"a","budget":10.00,"regionTarget":["黑龙江"],"excludeIp":["1.3.3.3","1.3.33.0"],"negativeWords":["3232","培训"],"exactNegativeWords":["3232","培训"],"schedule":[{"weekDay":1,"startHour":1,"endHour":5}]}',
            '{"campaignName":"一二三四五六七八九十一二三四五","budget":10.0,"regionTarget":["北京"],"excludeIp":["1.3.3.3","1.3.33.0"],"negativeWords":["3232","培训"],"exactNegativeWords":["3232","培训"],"schedule":[{"weekDay":1,"startHour":1,"endHour":5}]}',
            '{"campaignName":"测试1","budget":40,"regionTarget":["北京"],"excludeIp":["1.3.3.3","1.3.33.0"],"negativeWords":["3232","培训"],"exactNegativeWords":["3232","培训"],"schedule":[{"weekDay":1,"startHour":1,"endHour":5}]}',
        ]
        self.session = requests.session()

    def jointUrl(self, x):
        return 'http://%s/%s' % (self.server, x.lstrip('/'))

    def jointData(self, x=None):
        if x is not None:
            return '{%s,%s}' % (x, self.extra_body)
        return '{%s}' % self.extra_body

    def testDeleteCampaign(self):
        self.prepareCampaigns()
        # Delete non-exist campaign
        ids = sorted(self.getAllCampaignID())
        ret = self.deleteCampaign([ids[-1] + 1])
        assert ret.status_code == 200, 'Test: Delete non-exist campaign\nResponse code should be 200, get %s' % ret.status_code
        header = ret.json()['header']
        assert header.get(
            'desc') == 'fail', 'Test: Delete non-exist campaign\nDeletion should be fail, but %s' % header.get('desc')
        if not ids:
            return

        # Delete one SINGLE campaign
        ret = self.deleteCampaign(ids[0:1])
        assert ret.status_code == 200, 'Test: Delete one single campaign %s\nResponse code should be 200, get %s' % (
            ids[0:1], ret.status_code)
        header = ret.json()['header']
        assert header.get('desc') == 'success', 'Test: Delete one single campaign %s\nDeletion should be success, but %s' % (
            ids[0:1], header.get('desc'))
        new_ids = sorted(self.getAllCampaignID())
        assert ids[0] not in new_ids, 'Test: Delete one single campaign %s\nDeletion should be success, but %s still exists' % (
            ids[0:1], ids[0])

        # Delete valid campaign ID + non-exit campaign ID
        ret = self.deleteCampaign(new_ids[0:1] + [-1, -2] + new_ids[1:])
        assert ret.status_code == 200, 'Test: Delete valid campaigns + non-exist campaign\nResponse code should be 200, get %s' % (
            ret.status_code)
        header = ret.json()['header']
        assert header.get(
            'desc') == 'partial fail', 'Test: Delete valid campaigns + non-exist campaign\nDeletion should be partial fail, but %s' % (header.get('desc'))
        new_ids = sorted(self.getAllCampaignID())
        assert len(
            new_ids) == 0, 'Test: Delete valid campaigns + non-exist campaign\nDeletion of valid campaign should be success, but %s exist' % (new_ids)

        # Delete all campaign ID
        self.prepareCampaigns()
        ids = sorted(self.getAllCampaignID())
        ret = self.deleteCampaign(ids)
        assert ret.status_code == 200, 'Test: Delete all campaigns\nResponse code should be 200, get %s' % (
            ret.status_code)
        header = ret.json()['header']
        assert header.get('desc') == 'success', 'Test: Delete all campaigns\nDeletion should be success, but %s' % (
            header.get('desc'))
        new_ids = sorted(self.getAllCampaignID())
        assert len(
            new_ids) == 0, 'Test: Delete all campaigns\nDeletion all campaigns, but %s exist' % (new_ids)

    def deleteCampaign(self, lst):
        lst = lst or []
        if isinstance(lst, list) is False:
            return None
        return self.session.request(
            method='DELETE',
            url=self.jointUrl('/api/campaign/deleteCampaign'),
            headers=self.headers,
            data='"body":{"campaignIds":%s}' % lst,
        )

    def prepareCampaigns(self, lst=None):
        lst = lst or self.campaigns
        ids = []
        for item in lst:
            campaigns = self.addCampaign(item).json().get(
                'body', {}).get('campaignTypes')
            if campaigns and 'campaignId' in campaigns[0]:
                ids.append(campaigns[0]['campaignId'])
        new_ids = self.getAllCampaignID()
        for item in ids:
            if item not in new_ids:
                return False, item
        return True

    def clearCampaigns(self):
        ids = self.getAllCampaignID()
        self.deleteCampaign(ids)
        if len(self.getAllCampaignID()) == 0:
            return True
        return False

    def addCampaign(self, js):
        return self.processRequest(
            method='post',
            url=self.jointUrl('/api/campaign/addCampaign'),
            headers=self.headers,
            data=self.jointData(js),
        )

    def testAddCampaign(self, js):
        # Assert success
        assertResponseCode(response, 200, 'success')
        # Failure
        ret = self.processRequest(**dct)
        assertResponseCode(response, 404, 'fail')

    def assertResponseCode(self, response, code=200, desc='success'):
        header = response.get('header')
        assert ret.status_code == code
        assert header.get('desc') == desc
        return header.get('body', header.get('failures', False))

    def testGetAllCampaignID(self):
        expected_ids = sorted(self.expectedAllCampaignID())
        ids = sorted(self.getAllCampaignID())
        assert ids == expected_ids, 'Expected %s, get %s' % (expected_ids, ids)

    def getAllCampaign(self):
        return self.processRequest(
            method='post',
            url=self.jointUrl('/api/campaign/getAllCampaign'),
            data=self.jointData(),
            headers=self.headers,
        )

    def getAllCampaignID(self):
        req = TestRequest(
            method='post',
            url=self.jointUrl('/api/campaign/getAllCampaignID'),
            data=self.jointData(),
            headers=self.headers,
            action=None,
        )
        return req.get_response().json().get('body', {}).get('campaignIds', [])

    def processRequest(self, request=None, **kwargs):
        if request is not None:
            return self.session.send(request.prepare())
        return self.session.request(**kwargs)

    def deleteCampaign(self, id_list=None):
        id_list = id_list or {}
        js = '{"body":{"campaignIds":%s},"header":{"username":"ShenmaPM2.5","password":"pd123456","token":"d789a6c8-e6d9-4d7c-bf16-0f518d6888b1"}}' % id_list
        urllink = '/api/campaign/deleteCampaign'
        response = requests.delete('http://%s/%s' % (self.server, urllink),
                                   headers=self.headers, data=js)
        return response

    def expectedAllCampaignID(self):
        response = self.getAllCampaign()
        campaigns = response.json().get('body', {}).get('campaignTypes', [])
        return [item['campaignId'] for item in campaigns if 'campaignId' in item]


def execute_case(conf_dict):
    '''
    1. Prepare Request
    2. Get Response
    3. Assertion
    '''
    # TODO: tie request to the conf_dict??
    request = TestRequest(method=conf_dict.get('HTTP_METHOD'),
                          url=conf_dict.get('HTTP_URL'),
                          headers=conf_dict.get('HTTP_HEADERS'),
                          data=conf_dict.get('HTTP_DATA'))
    response = request.get_response()

    conf_dict['_response'] = response.json()
    result = assert_object(response.json(), conf_dict.get('assert'))

    log.debug('Request  Data: %s' % request.data)
    log.debug('Response Json: %s' % conf_dict['_response'])

    print '{name} : [{result}]'.format(
        name=conf_dict.get('__name__').rjust(65, '-'),
        result='SUCCESS' if result is True else 'FAILURE')
    print 'DESC: {desc}'.format(desc=conf_dict.get('desc'))
    if result is not True:
        print 'URL     : %s' % conf_dict['HTTP_URL']
        print 'Request : %s' % request.data
        print 'Response: %s' % conf_dict['_response']
        print 'Expected: %s' % conf_dict.get('assert')
        if isinstance(result, AssertError):
            print 'Error   : %s' % result.msg


def main():
    _path = os.path.dirname(os.path.realpath(__file__))
    for file in os.listdir(os.path.join(_path, 'conf')):
        if file.endswith('.conf'):
            # TODO
            cf = SafeConfigParser(allow_no_value=True)
            case_generator = parse_config(
                os.path.join(_path, 'conf', file), CASE_PREFIX)
            try:
                while True:
                    case_dict = case_generator.next()
                    execute_case(case_dict)
            except StopIteration:
                pass


if __name__ == '__main__':
    pass
