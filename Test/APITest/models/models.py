# -*- coding: utf-8 -*-

from requests import Request, Session
import logging
import zipfile
import tarfile
import requests
from requests.exceptions import MissingSchema
import collections
from ..compat import BLANK, AttributeDict, APIAttributeDict, ReadOnlyObject, PersistentAttributeObject

import json
from functools import partial


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


class SlotsDict(PersistentAttributeDict):
    __classhook__ = AttributeDict

    def __init__(self, *args, **kwargs):
        # TODO: not compatible with nested dict
        _dict = {}
        for key in self.__slots__:
            _dict[key] = getattr(self.__class__, key, None)
        super(SlotsDict, self).__init__(_dict)
        super(SlotsDict, self).update(*args, **kwargs)

    def __setitem__(self, key, value):
        if key not in self.__slots__:
            raise KeyError(
                "%s.%s is not exist!" % (self.__class__, key))
        super(SlotsDict, self).__setitem__(key, value)
        super(SlotsDict, self).__setattr__(key, value)

    __setattr__ = __setitem__


def _slots_class(name, attributes):
    '''
    Solid attributes
    '''
    return SlotsMeta(name, (SlotsDict,), attributes)


class BaseData(object):
    _params_ = None
    allow_null = True

    def __init__(self, **kwargs):
        self._params_ = self._params_ or list(kwargs.iterkeys())
        for key in kwargs:
            if type(kwargs.get(key)) is dict:
                setattr(self, key, BaseData(**kwargs.get(key)))
            else:
                setattr(self, key, kwargs.get(key))

    def __str__(self):
        return self.json()

    def json(self, allow_null=None, params=None):
        return json.dumps(self.dict(allow_null, params))

    def dict(self, allow_null=None, params=None):
        if allow_null is None:
            _allow_null = self.allow_null
        else:
            _allow_null = allow_null
        params = params or self._params_ or []
        params_dict = {}
        for key in params:
            if not hasattr(self, key):
                continue
            value = getattr(self, key)
            if value is None and _allow_null is False:
                continue
            if isinstance(value, BaseData):
                params_dict[key] = value.dict(allow_null)
            else:
                params_dict[key] = value
        return params_dict

    def __call__(self, params=None, **kwargs):
        for key in kwargs:
            if key in params or hasattr(self, key):
                setattr(self, key, kwargs.get(key))
        return self

    def __eq__(self, obj):
        return (type(self) is type(obj) and
                self.dict() == obj.dict(params=self._params_))

    def __ne__(self, obj):
        return not self.__eq__(obj)


class RequestHeader(BaseData):
    _params_ = ['username', 'password', 'token', 'target']

    def __init__(self, username, password, token, target=None):
        self.username = username
        self.password = password
        self.token = token
        self.target = target


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


class BulkJobBody(BaseData):
    _params_ = ['bulkJobRequestType']
    '''
    campaignIds: long[], default = []
    singleFile: int in (0,1), default = 0
    format: int in (0,1), default = 0
    variableColumns: string[], default = []
    fileController: 9-bit, binary
    '''

    def __init__(self, campaignIds=None, singleFile=None, format=None, variableColumns=None, fileController=None):
        self.bulkJobRequestType = BaseData(
            campaignIds=campaignIds,
            singleFile=singleFile,
            format=format,
            variableColumns=variableColumns,
            fileController=fileController,
        )
        self.bulkJobRequestType._params_ = [
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
        if value == BLANK:
            # clear item
            return self.pop(key, BLANK)

        if isinstance(value, collections.MutableSequence):
            t = value[0] if value else None
        else:
            t = value
        # 这里需要用 value[0].__name__
        # 因为 instance.__name__ 和 class.__name__ 是不一样的
        if key == 'body'and issubclass(type(t), APIType) and hasattr(t, '__name__'):
            if t.__name__.endswith('s') and not isinstance(value, collections.MutableSequence):
                value = [value]
            super(APIDataMixin, self).__setitem__(key, {t.__name__: value})
        else:
            super(APIDataMixin, self).__setitem__(key, value)


class APIType(APIDataMixin):

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
        assert response.status_code == 200, 'Status code must be 200! not "%s"' % response.status_code
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
        log.debug('[RESPONSE] %s\n' % res.content)
        # For API, status code should be always `200`
        assert res.status_code == 200, \
            'Expected status `200`, got `{}`.\nURL:{}\nBody:{}\n'.format(
                res.status_code, res.request.url, res.request.body)
        return res

    def __call__(self, server=None, header=None, body=None, json=None, **kwargs):
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
