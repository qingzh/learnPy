# -*- coding:utf-8 -*-
from .model.models import ReadOnlyAttributeDict, RequestHeader, APIRequest

BLOCK_SIZE = 1 << 15

SERVER = 'http://42.120.168.74'

USERS = ReadOnlyAttributeDict({
    'ailetou': RequestHeader(**{
        "username": "",
        "password": "",
        "token": ""}),
    })
})


post = 'post'
delete = 'delete'

"""

1. 到底是直接配成一个 APIRequest object
2. 还是只记录 method, uri；需要的时候再装配 APIRequest

使用2, 可以方便复用同样的session, user, server；不需要每次都指定user,server
使用1. 是为了防止递归定义，让程序知道哪个是叶节点；否则会认为
getAllCampaignID.method 也是一个REST URI

"""
api_dict = {
    "campaign": {
        "getAllCampaignID": APIRequest(method=post, uri='/api/campaign/getAllCampaignID'),
        "getAllCampaign": APIRequest(method=post, uri='/api/campaign/getAllCampaign'),
        "getCampaignByCampaignId": APIRequest(method=post, uri='/api/campaign/getCampaignByCampaignId'),
        "updateCampaign": APIRequest(method=post, uri='/api/campaign/updateCampaign'),
        "deleteCampaign": APIRequest(method=delete, uri='/api/campaign/deleteCampaign'),
        "addCampaign": APIRequest(method=post, uri='/api/campaign/addCampaign')
    },
    "adgroup": {
        "getAllAdgroupId": APIRequest(method=post, uri='/api/adgroup/getAllAdgroupId'),
        "getAdgroupIdByCampaignId": APIRequest(method=post, uri='/api/adgroup/getAdgroupIdByCampaignId'),
        "getAdgroupByCampaignId": APIRequest(method=post, uri='/api/adgroup/getAdgroupByCampaignId'),
        "getAdgroupByAdgroupId": APIRequest(method=post, uri='/api/adgroup/getAdgroupByAdgroupId'),
        "addAdgroup": APIRequest(method=post, uri='/api/adgroup/addAdgroup'),
        "updateAdgroup": APIRequest(method=post, uri='/api/adgroup/updateAdgroup'),
        "deleteAdgroup": APIRequest(method=delete, uri='/api/adgroup/deleteAdgroup'),
    },
    "keyword": {
        "getKeywordIdByAdgroupId": APIRequest(method=post, uri='/api/keyword/getKeywordIdByAdgroupId'),
        "getKeywordByAdgroupId": APIRequest(method=post, uri='/api/keyword/getKeywordByAdgroupId'),
        "getKeywordByKeywordId": APIRequest(method=post, uri='/api/keyword/getKeywordByKeywordId'),
        "getKeywordStatus": APIRequest(method=post, uri='/api/keyword/getKeywordStatus'),
        "getKeyword10Quality": APIRequest(method=post, uri='/api/keyword/getKeyword10Quality'),
        "addKeyword": APIRequest(method=post, uri='/api/keyword/addKeyword'),
        "updateKeyword": APIRequest(method=post, uri='/api/keyword/updateKeyword'),
        "deleteKeyword": APIRequest(method=delete, uri='/api/keyword/deleteKeyword'),
        "activateKeyword": APIRequest(method=post, uri='/api/keyword/activateKeyword'),
    },
    "creative": {
        "getCreativeIdByAdgroupId": APIRequest(method=post, uri='/api/creative/getCreativeIdByAdgroupId'),
        "getCreativeByAdgroupId": APIRequest(method=post, uri='/api/creative/getCreativeByAdgroupId'),
        "getCreativeByCreativeId": APIRequest(method=post, uri='/api/creative/getCreativeByCreativeId'),
        "getCreativeStatus": APIRequest(method=post, uri='/api/creative/getCreativeStatus'),
        "addCreative": APIRequest(method=post, uri='/api/creative/addCreative'),
        "updateCreative": APIRequest(method=post, uri='/api/creative/updateCreative'),
        "deleteCreative": APIRequest(method=delete, uri='/api/creative/deleteCreative'),
        # 区别于activate keywords
        "activeCreative": APIRequest(method=post, uri='/api/creative/activeCreative'),
    },
    "newCreative": {
        "getSublinkIdByAdgroupId": APIRequest(method=post, uri='/api/newCreative/getSublinkIdByAdgroupId'),
        "getSublinkBySublinkId": APIRequest(method=post, uri='/api/newCreative/getSublinkBySublinkId'),
        "addSublink": APIRequest(method=post, uri='/api/newCreative/addSublink'),
        "updateSublink": APIRequest(method=post, uri='/api/newCreative/updateSublink'),

        # 删除任何指定的附加创意都用此方法
        "deleteSublink": APIRequest(method=delete, uri='/api/newCreative/deleteSublink'),

        "getPhoneIdByAdgroupId": APIRequest(method=post, uri='/api/newCreative/getPhoneIdByAdgroupId'),
        "getPhoneByPhoneId": APIRequest(method=post, uri='/api/newCreative/getPhoneByPhoneId'),
        "addPhone": APIRequest(method=post, uri='/api/newCreative/addPhone'),
        "updatePhone": APIRequest(method=post, uri='/api/newCreative/updatePhone'),

        "getAppIdByAdgroupId": APIRequest(method=post, uri='/api/newCreative/getAppIdByAdgroupId'),
        "getAppByAppId": APIRequest(method=post, uri='/api/newCreative/getAppByAppId'),
        "addApp": APIRequest(method=post, uri='/api/newCreative/addApp'),
        "updateApp": APIRequest(method=post, uri='/api/newCreative/updateApp'),
    },
    "bulkJob": {
        "getAllObjects": APIRequest(method=post, uri='/api/bulkJob/getAllObjects'),
    },
    "task": {
        "getTaskState": APIRequest(method=post, uri='/api/task/getTaskState')
    },
    "file": {
        "download": APIRequest(method=post, uri='/api/file/download')
    },
}

api = ReadOnlyAttributeDict(api_dict)


class Campaign(object):

    @property
    def getAllCampaignID(self):
        return APIRequest(uri='/api/campaign/getAllCampaignID')

    @property
    def deleteCampaign(self):
        return APIRequest(uri='/api/campaign/deleteCampaign', method='delete')

    @property
    def getAllCampaign(self):
        return APIRequest(uri='/api/campaign/getAllCampaign')

    @property
    def addCampaign(self):
        return APIRequest(uri='/api/campaign/addCampaign')

    @property
    def getCampaignByCampaignId(self):
        return APIRequest(uri='/api/campaign/getCampaignByCampaignId')


class Task(object):

    @property
    def getTaskState(self):
        '''
        return a new object when called
        '''
        return APIRequest(uri='/api/task/getTaskState')
    """
    @getTaskState.setter
    def getTaskState(self, header=None, body=None, method=None):
        '''
        return a new object when called
        '''
        return APIRequest(uri='/api/task/getTaskState', heder=heder, body=body, method=method)
    """


class BulkJob(object):

    @property
    def getAllObjects(self):
        '''
        return a new object when called
        '''
        return APIRequest(
            uri='/api/bulkJob/getAllObjects')
    """
    @getAllObjects.setter
    def getAllObjects(self, header=None, body=None, method=None):
        '''
        return a new object when called
        '''
        return APIRequest(uri='/api/bulkJob/getAllObjects', heder=heder, body=body, method=method)
    """


class File(object):

    @property
    def download(self):
        '''
        return a new object when called
        '''
        return APIRequest(
            uri='/api/file/download')
    """
    @downlod.setter
    def downlod(self, header=None, body=None, method=None):
        '''
        return a new object when called
        '''
        return APIRequest(
            uri='/api/file/download', heder=heder, body=body, method=method)
    """

    '''
class API(object):
    @property
    def bulkJob(self):
        # Singletion
        if hasattr(self, '_bulkjob') is False:
            self._bulkjob = BulkJob()
        return self._bulkjob

    @property
    def task(self):
        # Singletion
        if hasattr(self, '_task') is False:
            self._task = Task()
        return self._task

    @property
    def file(self):
        # Singletion
        if hasattr(self, '_file') is False:
            self._file = File()
        return self._file

    @property
    def campaign(self):
        if hasattr(self, '_campaign') is False:
            self._campaign = Campaign()
        return self._campaign
    '''
