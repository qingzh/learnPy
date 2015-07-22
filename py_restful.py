import requests
import json
from .models import AttributeDict
from requests import Request

requests.models.json_dumps = json_dump_decorator(json.dumps)


def response_hook(obj):
    def response_wrapper(response, *args, **kwargs):
        try:
            response.body = json.loads(response.content, object_hook=obj)
        except Exception:
            pass
    return response_wrapper


class APIRequest(Request):

    def __init__(self, uri=None, **kwargs):
        '''
        API request body is json-object
        '''
        super(APIRequest, self).__init__(**kwargs)
        if not self.headers:
            self.headers = {'Content-Type': 'Application/json'}
        self._uri = uri
        self.hooks['response'] = response_hook(AttributeDict)

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
        if server:
            self.url = server + self.uri
        if session is None:
            session = Session()
        self.__dict__.update(kwargs)
        try:
            prepared = self.prepare()
        except MissingSchema:
            self.url = 'http://' + self.url
            print self.url
            prepared = self.prepare()
        return session.send(prepared, stream=stream)

    def __call__(self, **kwargs):
        self.__dict__.update(kwargs)
        return self
