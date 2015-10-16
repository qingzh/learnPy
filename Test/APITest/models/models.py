# -*- coding: utf-8 -*-

from requests import Request, Session
import logging
import zipfile
import tarfile
import requests
from requests.exceptions import MissingSchema
from ..compat import (
    SlotsDict, is_sequence, BLANK, AttributeDict,
    APIAttributeDict, ReadOnlyObject, PersistentAttributeObject)

import json
from functools import partial

__all__ = [
    'JSONEncoder', 'ReadOnlyAttributeDict', 'PersistentAttributeDict',
    'SlotsMeta', '_slots_class', 'APIType', 'APIData', 'zipORtar']


class JSONEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return dict(obj)
        except TypeError:
            raise TypeError(
                '%s.%s is NOT dict serializable', obj.__module__, obj.__name__)

requests.models.json_dumps = partial(json.dumps, cls=JSONEncoder)

log = logging.getLogger(__name__)

SEQUENCE_TYPE = (list, tuple, set)


def sample(x, y):
    '''
    get subdict from dict `y` where `y.keys()` == x
    >>> d = {'a':1, 'b':2, 'c':3, 'd':4}
    >>> sample(['c', 'd'], d)
    {'c': 3, 'd': 4}
    '''
    return dict((i, y[i]) for i in x if i in y)


class ReadOnlyAttributeDict(ReadOnlyObject, APIAttributeDict):

    pass


class PersistentAttributeDict(PersistentAttributeObject, APIAttributeDict):
    pass


class SlotsMeta(type):

    def __new__(cls, name, bases, attrs):
        # attrs maybe a list
        if isinstance(attrs, SEQUENCE_TYPE):
            attrs = dict.fromkeys(attrs, None)
        attrs['__slots__'] = tuple(attrs)
        return super(SlotsMeta, cls).__new__(cls, name, bases, attrs)


def _slots_class(name, attributes):
    '''
    Solid attributes
    '''
    return SlotsMeta(name, (SlotsDict,), attributes)


class RequestData(SlotsDict):
    __slots__ = ['body', 'header']


class ResponseData(AttributeDict):
    __classhook__ = AttributeDict

    @property
    def messages(self):
        '''
        failures.message
        '''
        if 'failures' in self.header:
            return [x.get('message') for x in self.header.failures]
        return None

    @property
    def codes(self):
        '''
        failures.code
        '''
        if 'failures' in self.header:
            return [x.get('code') for x in self.header.failures]
        return None

    @property
    def status(self):
        return self.header.status


class BulkJobBody(SlotsDict):
    __slots__ = ['bulkJobRequestType']
    __classhook__ = AttributeDict
    '''
    campaignIds: long[], default = []
    singleFile: int in (0,1), default = 0
    format: int in (0,1), default = 0
    variableColumns: string[], default = []
    fileController: 9-bit, binary
    '''

    def __init__(self, campaignIds=None, singleFile=None, format=None,
                 variableColumns=None, fileController=None):
        self.bulkJobRequestType = SlotsDict(
            campaignIds=campaignIds,
            singleFile=singleFile,
            format=format,
            variableColumns=variableColumns,
            fileController=fileController,
        )
        self.bulkJobRequestType.__slots__ = [
            'campaignIds', 'singleFile',
            'format', 'variableColumns', 'fileController']


class APIResponse(AttributeDict):

    def __init__(self, *args, **kwargs):
        super(APIResponse, self).__init__(*args, **kwargs)

    def messages(self):
        raise Exception('Undefined')


class APIDataMixin(AttributeDict):

    '''
    turn `apiType` to json string:
    "apiTypes":[apiType]
    '''
    __classhook__ = AttributeDict

    def __init__(self, *args, **kwargs):
        """
        take care of nested dict
        """
        super(AttributeDict, self).__init__(*args, **kwargs)
        for key, value in self.iteritems():
            # Nested AttributeDict object
            # new object should be instance of self.__class__
            self.__setitem__(key, value)

    def __setitem__(self, key, value):
        '''
        如果类型名称是复数，例如 campaignTypes 则自动将值转化为数组
        否则转化为字符串类型，例如 accountInfoType
        '''
        if value == BLANK:
            # clear item
            return self.pop(key, BLANK)

        if is_sequence(value):
            t = value[0] if value else None
        else:
            t = value
        # 这里需要用 value[0].__name__
        # 因为 instance.__name__ 和 class.__name__ 是不一样的
        if key == 'body'and isinstance(t, NamedMixin) \
                and hasattr(t, '__name__'):
            if t.__name__.endswith('s') and not is_sequence(value):
                # 防止 dict 类型变成 dict.keys() ...
                value = [value]
            super(APIDataMixin, self).__setitem__(key, {t.__name__: value})
        else:
            super(APIDataMixin, self).__setitem__(key, value)


class NamedMixin(object):

    ''' 用于拼装 TypeName 
    例如: 
    >>> body=AdgroupType
    adgroupTypes:[AdgroupType]
    >>> body=[AdgroupType,AdgroupType]
    adgroupTypes: [AdgroupType, AdgroupType]
    '''
    pass


class APIType(APIDataMixin, NamedMixin):

    '''
    turn `apiType` to json string:
    "apiTypes":[apiType]
    '''

    pass


class APIData(APIDataMixin):

    pass


def response_hook(obj):
    def response_wrapper(response, *args, **kwargs):
        # 2015年8月5日定论，所有返回码都必须是200,
        # status code 在 hook 里统一验证，不再放到单独的Assertion里
        assert response.status_code == 200, 'Expected status `200`'\
            ', got `{}`.\nURL:{}\nBODY:{}\nRES:{}'.format(
                response.status_code, response.request.url,
                response.request.body, response.content)
        try:
            response._body = obj(response.json())
            response.header = response._body.header
            if 'body' in response._body:
                response.body = response._body.body
            if 'failures' in response.header:
                response.codes = response._body.codes
                response.messages = response._body.messages
        except Exception:
            pass
    return response_wrapper


class APIRequest(Request):

    def __init__(self, uri=None, **kwargs):
        '''
        API request body is json-object
        '''
        super(APIRequest, self).__init__(**kwargs)
        '''
        # `json=data` will set the headers automatically
        if not self.headers:
            self.headers = {'Content-Type': 'Application/json'}
        '''
        self._uri = uri
        self.hooks['response'] = response_hook(ResponseData)

    def set_hook(self, obj):
        self.hooks['response'] = response_hook(obj)

    @property
    def uri(self):
        '''
        read only
        '''
        return self._uri

    @property
    def server(self):
        return self._server

    '''
    def prepare(self):
        if isinstance(self.json, BaseData):
            self.json = self.json.dict()
        return super(APIRequest, self).prepare()
    '''

    def response(self, server=None, session=None, stream=False, **kwargs):
        '''
        `json=data`
        '''
        if server:
            self.url = server + self.uri
        if session is None:
            session = Session()
        self.__dict__.update(kwargs)
        try:
            prepared = self.prepare()
        except MissingSchema:
            self.url = 'http://' + self.url
            prepared = self.prepare()
        res = session.send(prepared, stream=stream)
        log.debug(res.request.url)
        log.debug('[REQUEST ] %s' % res.request.body)
        log.debug('[RESPONSE] %s' % res.content)
        # For API, status code should be always `200`
        assert res.status_code == 200, 'Expected status `200`'\
            ', got `{}`.\nURL:{}\nBody:{}\nRESP:{}'.format(
                res.status_code, res.request.url,
                res.request.body, res.contents)
        return res

    def __call__(self, server=None, header=None, body=None,
                 json=None, **kwargs):
        if header is not None:
            json = APIData(header=header, body=body)
        return self.response(json=json, server=server, **kwargs)


class TestRequest(Request):

    def __init__(self, **kwargs):
        ''' VALID Arguments
        :param method: HTTP method to use.
        :param url: URL to send.
        :param headers: dictionary of headers to send.
        :param data: the body to attach to the request. If a dictionary is provided, form-encoding will take place.
        :param json: json for the body to attach to the request (if data is not specified).
        :param params: dictionary of URL parameters to append to the URL.
        :param auth: Auth handler or (user, pass) tuple.
        :param cookies: dictionary or CookieJar of cookies to attach to this request.
        :param hooks: dictionary of callback hooks, for internal usage.
        '''
        _super_init_ = super(TestRequest, self).__init__
        func_code = _super_init_.im_func.func_code
        self._req_kwargs = func_code.co_varnames[:func_code.co_argcount]
        _super_init_(**sample(self._req_kwargs, kwargs))
        log.debug('%s %s %s' % (self.method, self.url, self.data))

    def get_response(self, session=None, stream=False):
        session = session or self.session
        return session.send(self.prepare(), stream=stream)

    def __call__(self, **kwargs):
        for key in sample(self._req_kwargs, kwargs):
            setattr(self, key, kwargs.get(key))
        return self

    @property
    def session(self):
        if hasattr(self, '_session') is False:
            self._session = Session()
        return self._session


class BadFileError(Exception):
    pass


class zipORtar(object):

    '''
    map zipfile.ZipFile to tarfile.TarFile
    '''
    @classmethod
    def open(cls, name, mode):
        if zipfile.is_zipfile(name):
            cls.file = zipfile.ZipFile(name, mode)
            cls.file.getnames = cls.file.namelist
            cls.file.extractfile = cls.file.open
        elif tarfile.is_tarfile(name):
            cls.file = tarfile.open(name, mode)
        else:
            raise BadFileError(
                'Download file is not .zip or .gz: %s' % name)
        return cls.file
