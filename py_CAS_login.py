
import requests
from lxml import etree


_encode_params = requests.PreparedRequest._encode_params


headers = {
    #'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    #'Accept-Encoding': 'gzip, deflate',
    #'Accept-Language': 'zh-CN,zh;q=0.8',
    #'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Length': '0',
    'Content-Type': 'application/x-www-form-urlencoded',
    # 'Cookie': r.headers.get('set-cookie'),
    #'Host': '',
    # 'Origin': 'http://',
    # 'Referer': 'http://',
    #'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36'
}


def prepare_cookies(s, server, username, password, headers=headers):
    '''
    @param s: session
    @param server: server address
    @param username: username
    @param password: password
    @return cookies of login account

    >>> s = requests.Session()
    >>> cookies = prepare_cookies(s, 'http://xx.xx.xx', 'user_abc', 'password_123')

    '''
    r = s.get(server)
    page = etree.HTML(r.content)
    payload = {}
    for e in page.xpath('//input'):
        payload[e.get('name')] = e.get('value')
    payload.update(
        username=username,  password=password,  captchaResponse='1')

    data = _encode_params(payload)
    s.post(
        r.url, headers=headers, verify=False, params=r.cookies, data=data)
    return s.cookies
