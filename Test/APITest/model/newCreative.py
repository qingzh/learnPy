# -*- coding:utf-8 -*-

from .models import APIType, AttributeDict
from TestCommon.utils import gen_chinese_unicode


class TYPE(object):
    APP = 2
    SUBLINK = 0
    PHONE = 1


class SublinkInfo(APIType):
    # 单条推广子链的数据类型

    def __init__(self, description=None, descriptionUrl=None):
        # required. 子链的描述， length in [8,16]
        self.description = description
        # required. scheme in [http://, https://]
        self.destinationUrl = descriptionUrl or ''


class SublinkType(APIType):
    __name__ = 'sublinkTypes'

    def __init__(self, sublinkId=None, sublinkInfos=[], adgroupId=None, pause=None, status=None):
        self.sublinkId = sublinkId
        # 推广子链集合，需要2-4条子链，总长度<=32个字符(16个汉字)
        self.sublinkInfos = sublinkInfos
        # 推广单元ID，每个单元只能有一个子链
        self.adgroupId = adgroupId
        # 物料初始状态: True 暂停, False 启用
        self.pause = pause
        # 推广子链属性，不可改变，由系统指定
        self.status = status


def gen_sublinkInfo(desc, url):
    '''
    @param
    '''
    return SublinkInfo(desc, url)


def _gen_sublinkInfos(m, url=''):
    ret = []
    for i in range(m):
        ret.append(SublinkInfo(gen_chinese_unicode(8), url + '/%d' % i))
    return ret


def yield_sublinkType(n=1, adgroupId=None, url=''):
    '''
    @param id: adgroup id
    '''
    for i in xrange(n):
        # salt = datetime.now().strftime('%Y%m%d%H%M%S%f')
        m = i % 4 + 1  # amount of sublinkInfos
        yield SublinkType(
            sublinkInfos=_gen_sublinkInfos(m, url),
            adgroupId=adgroupId,
            pause=i & 1
        )


class GroupSublinkId(APIType):

    '''
    按单元ID分组的计算机推广子链id集合
    仅供接口返回使用
    '''

    def __init__(self, adgroupId, sublinkIds=[]):
        # 推广单元ID
        self.adgroupId = adgroupId
        # Array, 该单元下的推广子链ID集合
        self.sublinkIds = sublinkIds


class PhoneType(APIType):
    __name__ = 'phoneTypes'

    def __init__(self, phoneId=None, phoneNum=None, adgroupId=None, pause=None, status=None):
        # long, 电话ID
        self.phoneId = phoneId
        # string, 电话号码
        self.phoneNum = phoneNum
        # long, 单元ID
        self.adgroupId = adgroupId
        self.pause = pause
        self.status = status


class GroupPhoneId(APIType):

    '''
    按单元ID分组的计算机推广子链id集合
    仅供接口返回使用
    '''

    def __init__(self, adgroupId=None, phoneIds=[]):
        # 推广单元ID
        self.adgroupId = adgroupId
        # Array, 该单元下的推广子链ID集合
        self.phoneIds = phoneIds


class AppType(APIType):
    __name__ = 'appTypes'

    '''
    类型示例：
    {"appId":0,"adgroupId":72079694,"appName":"APP","imgFormat":"png","appLogo":"","downloadAddrIOS":"http://www.pzoom.com","downloadAddrAndroid":null,"detailAddrAndroid":null,"pause":false,"status":null}
    '''

    def __init__(self, appId=None, adgroupId=None, appName=None, imgForamt=None, appLogo=None, downloadAddrIOS=None, downloadAddrAndroid=None, detailAddrAndroid=None, pause=None, status=None):
        #----------------------------------------------------
        #  required

        # long, 单元ID
        self.adgroupId = adgroupId
        # string, App名称
        self.appName = appName
        # Byte[], appLogo
        self.appLogo = appLogo

        # IOS下载地址 和 Android下载地址；至少存在一个
        # string, IOS下载地址
        self.downloadAddrIOS = downloadAddrIOS
        # string, ANdroid下载地址
        self.downloadAddrAndroid = downloadAddrAndroid
        # string, Android详情地址
        self.detailAddrAndroid = detailAddrAndroid

        #----------------------------------------------------
        #  optional

        # string, 图片格式，仅支持{jpg, png}，默认 png
        # 此接口仅在接口输入时使用
        self.imgFormat = imgForamt  # optional
        self.pause = pause

        #----------------------------------------------------
        #  not editable

        # long,APP ID
        self.appId = appId
        self.status = status


class GroupAppId(APIType):

    '''
    按单元ID分组的计算机推广子链id集合
    仅供接口返回使用
    '''

    def __init__(self, adgroupId=None, appIds=[]):
            # 推广单元ID
        self.adgroupId = adgroupId
        # Array, 该单元下的推广子链ID集合
        self.appIds = appIds


class DeleteType(AttributeDict):

    '''
    DELETE /api/newCreative/deleteSublink

    sublinkIds: 要删除的创意ID列表
    newCreativeType: 要删除的创意类型

    为什么要叫 sublinkIds ? 因为 PM 这么定的……
    '''

    def __init__(self, sublinkIds=None, newCreativeType=None):
        # 这样的话怎么表达：null 这个概念？
        # 因为如果值为 None 的话，这个域就不存在
        if sublinkIds:
            self.sublinkIds = sublinkIds
        if newCreativeType:
            self.newCreativeType = newCreativeType
