from ..schemas.common import Table, fields


class User(Table):
    userId = fields.IntField(description="用户账号")
    groupId = fields.IntField(description="用户通知群号")
    uid = fields.IntField(description="用户ID", null=True)
    nickname = fields.CharField(max_length=120, description="用户昵称", null=True, default="")
    avatar = fields.CharField(max_length=255, description="用户头像", null=True, default="")
    token = fields.CharField(max_length=64, description="学习强国token", null=True, default="")
    expires = fields.IntField(description="Token过期时间戳", null=True, default=0)
    score = fields.FloatField(default=0.0, description="总积分")
    auto = fields.BooleanField(default=True, description="自动开始学习")

    class Meta:
        table = "user"
        description = "用户表"


class TodayScore(Table):
    user = fields.ForeignKeyField("models.User", null=True, on_delete=fields.SET_NULL, description="用户")
    totalScore = fields.IntField(description="当日积分", default=0)
    hasRead = fields.IntField(description="当日阅读得分", default=0)
    maxRead = fields.IntField(description="当日最多阅读得分", default=12)
    hasVideo = fields.IntField(description="当日视频得分", default=0)
    maxVideo = fields.IntField(default=12, description="当日最多视频得分")
    hasLogin = fields.IntField(default=0, description="每日登录")
    maxLogin = fields.IntField(description="每日登录最多得分", default=1)
    hasExam = fields.IntField(description="当日练习得分", default=0)
    maxExam = fields.IntField(description="当日最多练习得分", default=5)
    status = fields.SmallIntField(default=0, description="状态 1完成 0未完成")

    class Meta:
        table = "todayScore"
        description = "用户每日积分表"
