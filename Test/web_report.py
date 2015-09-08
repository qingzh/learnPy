#! -*- coding:utf8 -*-

import requests
from TestCommon.models.httplib import *
from TestCommon.utils import gen_files
from requests.utils import unquote

#######################################################################
#
'''
TODO
用中文文件名的话，传输文件的时候会有些问题，出在 'extension' 参数上
现在先暂时使用英文文件名
'''
KEYWORD_FILE = u'e:/doc/批量导入/tools_keyword.xls'
'''
{
  "status": "success",
  "wolongError": null,
  "data": "http://42.120.168.65/fs/wuliao/66755/wuliao_66755_95e5d03b9516d4f868d1663fe076daee.xls",
  "extension": "tools_keyword.xls"
}
'''
CREATIVE_FILE = u'e:/doc/批量导入/tools_creative.xlsx'
'''
{
  "status": "success",
  "wolongError": null,
  "data": "http://42.120.168.65/fs/wuliao/66755/wuliao_66755_229ed4a28992595108132704bc3c704d.xlsx",
  "extension": "tools_creative.xlsx"
}
'''
#
#######################################################################

server = '42.120.168.65'
s = HttpServer(requests.Session(), server, 'wolongtest', 'pd123456')
s.prepare_cookies()


def upload_file(filename):
    '''
    @return res.json()
    '''
    files = gen_files(filename)
    url = s.server + '/fs/upload?uid=66755&utilType=WuliaoFile'
    res = s.session.post(url, files=files)
    assert res.status_code == 200
    return res.json()


def import_task(d):

    url = s.server + '/fs/porter/user/66755/import'
    res = s.session.post(
        url,
        params={
            'uid': 66755, 'type': 'keyword', 'override': 'false', 'fileName': d['extension']},
        data=d['data'])
    assert res.status_code == 200
    return res.json()
