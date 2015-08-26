# -*- coding:utf-8 -*-

from .models import APIType, APIData
from .const import IDTYPE
from TestCommon.models.const import BLANK


class CreativeType(APIType):
    __name__ = 'creativeTypes'

    def __init__(self, creativeId=BLANK, adgroupId=BLANK, title=BLANK, description1=BLANK, destinationUrl=BLANK, displayUrl=BLANK, pause=BLANK, status=BLANK):
        self.creativeId = creativeId
        # 推广单元ID，每个单元最多50个创意
        self.adgroupId = adgroupId
        # 标题：8-50字节；1个中文=2个字节
        self.title = title
        # 描述: 8-120字节
        self.description1 = description1
        # 目标URL：必须包含schema，最长1017个字符；域名与账户网站域名相同
        self.destinationUrl = destinationUrl
        # 显示URL：不包含schema, 最长36个字符；不能带'/'，不能包含中文
        self.displayUrl = displayUrl
        # 物料初始状态: True 暂停, False 启用
        self.pause = pause
        # 推广子链属性，不可改变，由系统指定
        self.status = status


class GroupCreative(APIData):

    '''
    按单元ID分组的计算机推广子链id集合
    仅供接口返回使用
    '''
    __classhook__ = CreativeType

    def __init__(self, adgroupId, creativeTypes):
        # 推广单元ID
        self.adgroupId = adgroupId
        # Array, 该单元下的创意对象集合
        self.creativeTypes = creativeTypes


class GroupCreativeId(APIData):

    def __init__(self, adgroupId, creativeIds):
        # 推广单元ID
        self.adgroupId = adgroupId
        # Array, 该单元下的创意ID集合
        self.creativeIds = creativeIds


class StatusType(APIData):

    '''
    按单元ID分组的计算机推广子链id集合
    仅供接口返回使用
    '''

    def __init__(self, id, adgroupId, campaignId, status):
        # 对象ID, 即创意id
        self.id = id
        # 推广单元ID
        self.adgroupId = adgroupId
        # 推广计划ID
        self.campaignId = campaignId
        # 该对象的状态
        # 0：暂停推广；1：审核中；2：不宜推广；5：推广中
        self.status = status


class GroupId(APIType):

    def __init__(self, ids, type):
        # ID数组，值为null时表示获取全账户关键词
        self.ids = ids
        # 枚举，值为 IDTYPE
        self.type = type
