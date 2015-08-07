#! /usr/bin/python
import sys
import re
import requests

DATA = None
DEAL = []
URL_PATTERN = 'http://www.gnc.com/cms_widgets/{0}/{1}/{2}_assets/c1.jpg'


def get_todayGNC():
    page = requests.get("http://www.gnc.com", timeout=10)
    print '---- %s ----' % page.headers.get('date')
    match = re.search(r'"gnc_home_1":[\D]+([\d]+)', page.text)
    if match:
        return int(match.group(1))
    page.close()
    return 0


def find_next_index(index, range_=2000):
    for i in xrange(0, range_):
        ntos = str(index + i)
        url = URL_PATTERN.format(ntos[0:2], ntos[2:4], ntos)
        try:
            # print '%s: %s' % (i, url)
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                DEAL.append(url)
                print url
        except:
            pass
    print DEAL


if __name__ == '__main__':
    index = get_todayGNC()
    if index == 0:
        exit('Parse Error: %d', index)
    else:
        print 'Start from: %d' % index
        find_next_index(index)
