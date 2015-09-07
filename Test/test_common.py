# -*- coding: utf-8 -*-

import os
import re
import json
from APITest.utils import (
    timeout_alert, len_unicode, assert_object, AssertError)
from APITest import utils
import logging
from APITest.model.models import log_stdout
from APITest.settings import api

###### Set logger output to stdout ######
utils.log.setLevel(logging.INFO)
log_stdout.setLevel(logging.INFO)
# utils.log.addHandler(log_stdout)

show = logging.getLogger(__name__)
show.setLevel(logging.INFO)
output_file = logging.FileHandler('%s.log' % __name__, 'w')
output_file.setLevel(logging.INFO)
# log out to `temp.log` file
show.addHandler(output_file)
# log out to `sys.stdout`
show.addHandler(log_stdout)
#########################################

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


def test_by_case(req, case):
    desc, send, expect = case[0:3]
    fixed = len(desc) - len_unicode(desc)
    title = desc.ljust(LINE_LENGTH + fixed - 10)
    show.debug(send)
    response = req.response(server=SERVER, data=send)
    receive = response.content.strip(
    ) if response.status_code != 500 else '500'

    show.info('-' * LINE_LENGTH)
    try:
        ret = assert_object(json.loads(receive), json.loads(expect))
        if ret is not True:
            raise AssertError()
    except AssertError:
        global ERROR_AMOUNT
        ERROR_AMOUNT += 1
        show.info('%s[%s]', title, 'X'.center(7))
        show.info(u'[期望返回] %s', expect.decode('utf-8'))
        show.info(u'[实际返回] %s', receive.decode('utf-8'))
        case.append(receive)
    else:
        global RIGHT_AMOUNT
        RIGHT_AMOUNT += 1
        show.info('%s[%s]', title, 'SUCCESS')
        case.append(True)
    return True


if __name__ == '__main__':
    common_cases = get_cases(
        os.path.join(TEST_DIR, 'common', 'negative.cases'))

    for request in api.nodes:
        show.info('=' * LINE_LENGTH)
        show.info(request.uri)
        map(lambda x: test_by_case(request, x), common_cases)
    else:
        show.info('=' * LINE_LENGTH)
