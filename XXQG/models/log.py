from enum import IntEnum

from ..schemas.common import Table, fields


class LogType(IntEnum):
    """日志类型"""
    Login: int = 1
    """登录"""
    Read: int = 2
    """阅读"""
    Video: int = 3
    """视频"""
    Exam: int = 4
    """练习"""


class Log(Table):
    type = fields.IntEnumField(LogType, description="日志类型", default=LogType.Login)
    score = fields.IntField(description="获得积分", default=0)
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL, description="用户")
    index = fields.IntField(description="任务队列")

    class Meta:
        table = "log"
        description = "用户任务日志表"
