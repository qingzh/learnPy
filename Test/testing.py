# -*- coding: utf-8 -*-

"""
参数：
server: 服务器地址

读取配置：
testcases/{service}/settings

读取测试用例：
testcases/{service}/*.cases

主要功能：
1. 添加计划: addCampaign
2. 更新计划: updateCampaign
3. 根据id获取计划: getCampaignByCampaignId
4. 获取所有计划: getAllCampaign
5. 获取所有计划id: getAllCampaignID
6. ：/getProductAdsCampaignID

"""
import os
import re
import json
import yaml
from APITest.model.models import TestRequest
from APITest.utils import (
    timeout_alert, len_unicode, assert_object, AssertError)
from APITest import utils
import sys
import logging
from APITest.model.models import log_stdout
from APITest.model.map import yield_province_city


###### Set logger output to stdout ######
utils.log.setLevel(logging.INFO)
log_stdout.setLevel(logging.WARNING)
utils.log.addHandler(log_stdout)

show = logging.getLogger(__name__)
show.setLevel(logging.INFO)
log_stdout.setLevel(logging.INFO)
show.addHandler(log_stdout)
#########################################


class sql_data(object):
    pass

memcached = []

# use relative path
DIRECTORY = os.path.dirname(os.path.relpath(__file__))
TEST_DIR = os.path.join(DIRECTORY, 'APITest', 'testcases')
SERVICE = ['campaign']
SETTINGS_RE = re.compile(
    '^\s*(?P<quote>[\'"])(?P<uri>[^\'"]+)(?P=quote):\s*(?P<method>[^,]+),\s*(?P<filename>\S+)')
SERVER = 'https://e.sm.cn'
HEADERS = {'Content-Type': 'application/json'}
LINE_LENGTH = 80
ERROR_AMOUNT = 0
RIGHT_AMOUNT = 0
CITY_MAP = list(yield_province_city())


def get_service_dir(dirname, service=SERVICE):
    dir_list = []
    for i in service:
        if os.path.isdir(os.path.join(dirname, i)):
            dir_list.append(os.path.relpath(os.path.join(dirname, i)))
    return dir_list


def get_configs(dirname):
    filename = os.path.join(dirname, 'settings')
    settings = {}
    with open(filename, 'r') as f:
        '''
        for line in f.readlines():
            match = SETTINGS_RE.match(line)
            uri = match.group('uri').strip('\'" ')
            method = match.group('method').strip('\'" ')
            case_file = match.group('filename').strip('\'" ')
            cases_list.append((uri, method, os.path.join(dirname, case_file)))
        '''
        _dict = yaml.load(f.read())
        for key in _dict.viewkeys():
            settings[os.path.join(dirname, key)] = _dict.get(key)
    return settings


def delete_by_json(data):
    body = json.loads(data).get('body')
    if body is None:
        return False
    key = body.iterkeys().next().rstrip('s')
    memcached = filter(lambda x: x.get(key) not in body.get(key), memcached)


def update_by_json(data):
    global memcached
    body = json.loads(data).get('body')
    if body is None:
        return False
    memcached = body


def replace_string(s, pattern=None):
    if '{}' not in s or pattern is None:
        return s
    global memcached
    if pattern + 's' in memcached:
        campaignIds = json.dumps(memcached.get(pattern + 's'))
    else:
        campaignIds = json.dumps(
            [x.get(pattern) for x in memcached])
    new_s = s.replace('{', '{{').replace('}', '}}').replace(
        '{{}}', '{}').format(campaignIds)
    print new_s
    return new_s


def test_by_case(req, case, steps):
    if len(case) < 3:
        case.append({"ret": None})
    show.info('-' * LINE_LENGTH)
    fixed = len(case[0]) - len_unicode(case[0])
    title = case[0].ljust(LINE_LENGTH + fixed - 10)

    req_pair = zip(case[1::2], case[2::2])
    for i, step in enumerate(steps):
        response = req(
            url='{}/{}'.format(SERVER, step[0]),
            method=step[1], data=req_pair[i][0]).get_response()
        receive = response.content.strip(
        ) if response.status_code != 500 else '500'
        try:
            if response.request.method.lower() == 'delete' and response.status_code == 200:
                delete_by_json(req_pair[i][0])
            else:
                update_by_json(receive)
            s = replace_string(req_pair[i][1], 'campaignId')
            ret = assert_object(json.loads(receive), json.loads(s))
            if ret is not True:
                raise AssertError()
        except AssertError:
            global ERROR_AMOUNT
            ERROR_AMOUNT += 1
            show.info('%s[%s]', title, 'X'.center(7))
            show.info(u'[期望返回] %s', s.decode('utf-8'))
            show.info(u'[实际返回] %s', receive.decode('utf-8'))
            case.append(receive)
            break
    else:
        global RIGHT_AMOUNT
        RIGHT_AMOUNT += 1
        show.info('%s[%s]', title, 'SUCCESS')
        case.append(True)
    return True


def get_cases(filename):
    cases = []
    case = []
    with open(filename, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            if line.startswith('##') or not line.strip():
                continue
            if line.startswith('#'):
                if case:
                    cases.append(case)
                case = [line.strip()]
            elif line.strip():
                case.append(line.strip())
        if case:
            cases.append(case)
    return cases


@timeout_alert(0)
def test_by_filename(filename, steps):
    cases = []
    if filename.endswith('_negative.cases'):
        cases.extend(common_cases)
    cases.extend(get_cases(filename))
    show.info('=' * LINE_LENGTH)
    show.info('%s' % filename)
    # To keep-alive, we user the same Request obj
    req = TestRequest(
        headers=HEADERS)
    for case in cases:
        test_by_case(req, case, steps)
    else:
        show.info('=' * LINE_LENGTH)
    return cases


def test_main(dir_list):
    global ERROR_AMOUNT, RIGHT_AMOUNT
    ERROR_AMOUNT, RIGHT_AMOUNT = 0, 0
    for i in dir_list:
        settings = get_configs(i)
        for key in settings.iterkeys():
            test_dict[i] = test_by_filename(key, settings.get(key))
    else:
        show.info('=' * LINE_LENGTH)
    show.info('[SUCCESS]: %3d/%4d' %
              (RIGHT_AMOUNT, RIGHT_AMOUNT + ERROR_AMOUNT))
    show.info('[FAILURE]: %3d/%4d' %
              (ERROR_AMOUNT, ERROR_AMOUNT + RIGHT_AMOUNT))

if __name__ == '__main__':
    dir_list = get_service_dir(TEST_DIR, SERVICE)
    common_cases = get_cases(
        os.path.join(TEST_DIR, 'common', 'negative.cases'))
    test_dict = {}
    settings = get_configs(dir_list[0])
