from nonebot import get_driver
from nonebot.plugin import PluginMetadata

global_config = get_driver().config
from . import models, schemas, utils
from .config import Config, plugin_config

__plugin_meta__ = PluginMetadata(
    name="学习强国挂机",
    description="每天自动完成学习强国任务,29分/天",
    usage="login",
    type="application",
    homepage="https://github.com/YouthLearning/XXQG",
    supported_adapters={"~onebot.v11"},
    extra={
        'author': 'TeenStudyFlow',
        'version': '0.0.1',
        'priority': 50,
    },
    config=Config
)

DRIVER = get_driver()


@DRIVER.on_startup
async def startup():
    await utils.path.connect()


DRIVER.on_shutdown(utils.path.disconnect)
