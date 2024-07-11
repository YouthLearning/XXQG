from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    local_browser_path: str = ''
    """本地浏览器程序路径 仅支持谷歌浏览器和Edge浏览器"""


plugin_name = 'XXQG'
plugin_version = '0.0.1'
plugin_config = get_plugin_config(Config)
