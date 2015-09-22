#! -*- coding:utf8 -*-

'''
require:
    requests, lxml, selenium
'''

import os.path
from APITest.compat import ThreadLocal
import test_account
#import test_adgroup
#import test_keyword
#import test_creative
#import test_newCreative
import traceback
import threading
import logging
from datetime import datetime
from APITest import RESULT_DIR, LOCKS, AttributeDict
import json

logging.basicConfig(
    level=logging.INFO,
    format='[%(threadName)-9s] %(message)s')

D = locals()


def show(t):
    logging.info(t.__dict__)


def main(server, user, flag):
    # set `local` config for Thread
    LOCKS.add(flag)
    threading.currentThread().setName(flag)

    ThreadLocal.SERVER = server
    ThreadLocal.USER = user
    ThreadLocal.create_time = datetime.now()

    for key in D.keys():
        if not key.startswith('test'):
            continue
        M = D[key]
        try:
            logging.info('Test %s', M.__name__)
            M.test_main()
        except Exception:
            traceback.print_exc()

    with open(os.path.join(RESULT_DIR, flag), 'w') as f:
        logging.info('Write results to %s', f.name)
        f.write(json.dumps(ThreadLocal.__dict__))

    LOCKS.remove(flag)


def get_results(flag):
    if not flag:
        return None
    if flag in LOCKS:
        return False

    with open(os.path.join(RESULT_DIR, flag), 'r') as f:
        logging.info('Get results from %s', f.name)
        s = f.read()

    return json.loads(s, object_hook=AttributeDict)


if __name__ == '__main__':
    show(ThreadLocal)
    t = threading.Thread(target=main, args=(ThreadLocal.SERVER, ThreadLocal.USER, datetime.now().strftime('%Y%m%d%H%M%S%f')))
    t.start()
    # ThreadLocal.format_with_ruby()
    # 注意：这里不要使用 u'中文'，直接 '中文' 即可
    logging.info(u'API回归测试')

