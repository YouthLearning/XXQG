from tortoise import fields, models


class Table(models.Model):
    """
    抽象模型
    """

    id = fields.UUIDField(pk=True, description="主键", autoincrement=True)
    status = fields.SmallIntField(default=1, description="状态 1有效 0禁用")
    created = fields.DatetimeField(auto_now_add=True, description="创建时间", null=True)
    modified = fields.DatetimeField(auto_now=True, description="更新时间", null=True)

    class Meta:
        abstract = True
        ordering = ["-created"]
        indexes = ("status",)
