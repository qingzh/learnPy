#! -*- coding:utf8 -*-

from .common import AttributeDict
from APITest.models.models import SlotsDict
from ..utils import prepare_url, is_sequence
import requests
import urlparse
from lxml import etree


class ServerInfo(AttributeDict):

    def __init__(self, username, password, userid, server):
        self.username = username
        self.password = password
        self.userid = userid
        self.server = server


class HttpServer(object):

    def __init__(self, session, server, username, password, headers=None):
        self.session = session
        self.server = server
        self.username = username
        self.password = password
        self.headers = headers
        self._assertion = None
        self.history = []

    @property
    def assertion(self):
        return self._assertion

    @assertion.setter
    def assertion(self, value):
        if value is None:
            return
        self._assertion = is_sequence(value, convert=True)

    @property
    def server(self):
        return self._server

    @server.setter
    def server(self, value):
        self._server = prepare_url(value)

    def __repr__(self):
        return repr(self.__dict__)

    def set_cookies_from_driver(self, driver):
        for cookie in driver.get_cookies():
            if 'expiry' in cookie:
                cookie['expires'] = cookie.pop('expiry')
            self.session.cookies.set_cookie(
                requests.cookies.create_cookie(**cookie))

    def prepare_cookies(self):
        '''
        @param session: session
        @param server: server address
        @param username: username
        @param password: password
        @return `RequestsCookieJar`: cookies of login account
        '''
        r = self.session.get(self.server, verify=False)
        assert r.status_code == 200, 'Failed to get page "%s": %d Error' % (
            self.server, r.status_code)
        page = etree.HTML(r.content)

        payload = {}
        for e in page.xpath('//input'):
            payload[e.get('name')] = e.get('value')
        payload.update(
            username=self.username,  password=self.password,  captchaResponse='1')

        res = self.session.post(
            r.url, verify=False, data=payload, headers=self.headers)
        assert 'login' not in res.url.lower(), 'Login failed!'

    @property
    def cookies(self):
        '''
        @return RequestsCookieJar: self.session.cookies
        '''
        if isinstance(self.session, requests.Session):
            return self.session.cookies
        return None

    def post(self, context, assertion=None):
        '''
        `POST` context to `customizedList.json`
        '''
        if assertion is None:
            assertion = self._assertion
        url = self._get_url(context)
        res = self.session.post(
            url, data=context.prepare(), headers=self.headers, verify=False)
        if assertion:
            for func in self._assertion:
                func(res, context)
        return res

    def _get_url(self, context):
        '''
        Produce the `customizedList.json` url

        | UserLevel | 1 | 账户 |
        | PlanLevel | 2 | 计划 |
        | UnitLevel | 3 | 单元|
        | WinfoLevel | 4 | 关键词 |
        | IdeaLevel | 5 | 创意 |
        | AppLevel | 8 | APP |
        | PhoneLevel | 9 | 电话 |
        | XiJingLevel | 10 | 蹊径 |
        '''
        # parsedUrl = urlparse.urlparse(server)
        # parsedUrl.scheme = parsedUrl.scheme or 'http'
        return urlparse.urljoin(
            self.server, '/cpc/%s/customizedList.json' % context.uri)


class PerformanceEntry(SlotsDict):
    _parsed = None
    _parsed_query = None
    __slots__ = ['secureConnectionStart',
                 'redirectStart',
                 'redirectEnd',
                 'name',
                 'startTime',
                 'domainLookupEnd',
                 'connectEnd',
                 'requestStart',
                 'initiatorType',
                 'responseEnd',
                 'fetchStart',
                 'duration',
                 'responseStart',
                 'entryType',
                 'connectStart',
                 'domainLookupStart',
                 '_parsed',
                 '_parsed_query']

    def __init__(self, *args, **kwargs):
        # TODO: not compatible with nested dict
        super(SlotsDict, self).__init__(*args, **kwargs)

    def __hash__(self):
        return hash(tuple(self.values()))

    @property
    def processingTime(self):
        return self.responseStart - self.requestStart

    @property
    def parsed(self):
        if self._parsed is None:
            self._parsed = urlparse.urlparse(self.name)
        return self._parsed

    @property
    def parsed_query(self):
        if self._parsed_query is None:
            self._parsed_query = AttributeDict(
                urlparse.parse_qs(self.parsed.query))
        return self._parsed_query
