#! -*- coding:utf8 -*-
#! -*- coding:utf8 -*-
'''
require:
    requests, lxml, selenium
'''
import os.path
import test_account
import test_campaign
import test_keyword
import test_creative
import test_newCreative
from APITest.compat import ThreadLocal
import traceback


def main(D):
    for key in D.keys():
        if not key.startswith('test'):
            continue
        M = D[key]
        try:
            M.test_main()
        except Exception:
            traceback.print_exc()

if __name__ == '__main__':
    main(locals())
    ThreadLocal.print_results()
