# -*- coding:utf-8 -*-

from .models import APIType, AttributeDict
from .const import IDTYPE
from TestCommon.models.const import BLANK


class KeywordType(APIType):
    __name__ = 'keywordTypes'

    def __init__(self, keywordId=BLANK, adgroupId=BLANK, keyword=BLANK, price=BLANK, destinationUrl=BLANK, matchType=BLANK, pause=BLANK, status=BLANK):
        # 关键词ID
        self.keywordId = keywordId
        # 推广单元ID，每个单元最多20000个关键词
        self.adgroupId = adgroupId
        # 关键词字面
        self.keyword = keyword
        # 关键词竞价价格, [0.3, 999.99] 并且 <= 所属计划预算
        self.price = price
        # 目标URL, 域名需与账户网站域名一致
        self.destinationUrl = destinationUrl
        # 匹配模式，0：精确匹配；1：短语匹配；2：广泛匹配
        self.matchType = matchType
        # 物料初始状态: True 暂停, False 启用
        self.pause = pause
        # 状态：0：暂停推广；1：审核中；2：不宜推广；7：推广中
        self.status = status


class GroupKeyword(AttributeDict):

    '''
    按单元ID分组的计算机推广子链id集合
    仅供接口返回使用
    '''

    def __init__(self, adgroupId, keywordTypes):
        # 推广单元ID
        self.adgroupId = adgroupId
        # Array, 该单元下的关键词对象集合
        self.keywordTypes = keywordTypes


class GroupKeywordId(AttributeDict):

    '''
    按单元ID分组的计算机推广子链id集合
    仅供接口返回使用
    '''

    def __init__(self, adgroupId, keywordIds):
        # 推广单元ID
        self.adgroupId = adgroupId
        # Array, 该单元下的关键词对象集合
        self.keywordIds = keywordIds


class GroupId(APIType):

    def __init__(self, ids, type):
        # ID数组，值为null时表示获取全账户关键词
        self.ids = ids
        # 枚举，值为 IDTYPE
        self.type = type


class KEYWORD_STATUS(object):
    PAUSE = 0
    AUDIT = 1
    REFUSE = 2


class StatusType(AttributeDict):
    __name__ = 'keywordStatus'

    def __init__(self, id, adgroupId, campaignId, status):
        # 关键词ID
        self.id = id
        # 该对象所属的单元ID
        self.adgroupId = adgroupId
        # 该对象所述的计划ID
        self.campaignId = campaignId
        # 状态：0：暂停推广；1：审核中；2：不宜推广；7：推广中
        self.status = status


class Quality10Type(AttributeDict):

    def __init__(self, id, adgroupId, campaignId, quality):
        # 该对象ID
        self.id = id
        # 该对象所属的单元ID
        self.adgroupId = adgroupId
        # 该对象所述的计划ID
        self.campaignId = campaignId
        # 该关键词的质量度，[0-10]
        self.quality = quality
