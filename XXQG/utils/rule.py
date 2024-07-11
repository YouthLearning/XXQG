from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg


async def must_command(order: Message = CommandArg()) -> bool:
    """
    限制指令后面不能加内容才生效
    :param order: 指令后面的内容
    :return: 返回True或False
    """
    if order:
        return False
    else:
        return True
