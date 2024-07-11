<div align="center">
    <img src="https://www.freeimg.cn/i/2023/12/03/656c227814852.png" alt="XXQG.png" border="0" width="500px" height="500px"/>
    <h1>XXQG</h1>
    <b>基于nonebot2和OneBotV11的学习强国自动插件，用于自动挂机，每日完成任务，29分/天</b>
    <br/>
    <a href="https://github.com/YouthLearning/XXQG/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/YouthLearning/XXQG?style=flat-square"></a>
    <a href="https://github.com/YouthLearning/XXQG/network"><img alt="GitHub forks" src="https://img.shields.io/github/forks/YouthLearning/XXQG?style=flat-square"></a>
    <a href="https://github.com/YouthLearning/XXQG/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/YouthLearning/XXQG?style=flat-square"></a>
    <a href="https://pypi.python.org/pypi/XXQG"><img src="https://img.shields.io/pypi/v/XXQG?color=yellow" alt="pypi"></a>
  	<a href="https://pypi.python.org/pypi/XXQG">
    <img src="https://img.shields.io/pypi/dm/XXQG" alt="pypi download"></a>
    <a href="https://github.com/YouthLearning/XXQG">
    <img src="https://views.whatilearened.today/views/github/YouthLearning/XXQG.svg" alt="Views"></a>
	<a href="https://github.com/YouthLearning/XXQG/blob/main/LICENSE"><img alt="GitHub license" src="https://img.shields.io/github/license/YouthLearning/XXQG?style=flat-square"></a>
    <a href="https://onebot.dev/">
    <img src="https://img.shields.io/badge/OneBot-v11-black?style=social&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABABAMAAABYR2ztAAAAIVBMVEUAAAAAAAADAwMHBwceHh4UFBQNDQ0ZGRkoKCgvLy8iIiLWSdWYAAAAAXRSTlMAQObYZgAAAQVJREFUSMftlM0RgjAQhV+0ATYK6i1Xb+iMd0qgBEqgBEuwBOxU2QDKsjvojQPvkJ/ZL5sXkgWrFirK4MibYUdE3OR2nEpuKz1/q8CdNxNQgthZCXYVLjyoDQftaKuniHHWRnPh2GCUetR2/9HsMAXyUT4/3UHwtQT2AggSCGKeSAsFnxBIOuAggdh3AKTL7pDuCyABcMb0aQP7aM4AnAbc/wHwA5D2wDHTTe56gIIOUA/4YYV2e1sg713PXdZJAuncdZMAGkAukU9OAn40O849+0ornPwT93rphWF0mgAbauUrEOthlX8Zu7P5A6kZyKCJy75hhw1Mgr9RAUvX7A3csGqZegEdniCx30c3agAAAABJRU5ErkJggg==" alt="onebot"></a>
    <a href="https://jq.qq.com/?_wv=1027&k=NGFEwXyS">
    <img src="https://img.shields.io/badge/QQ反馈群-511173803-orange?style=flat-square" alt="QQ Chat Group"></a>
	<a href="http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=2PQucjirnkHyPjoS1Pkr-ai2aPGToBKm">
    <img src="https://img.shields.io/badge/QQ体验群-821280615-orange?style=flat-square" alt="QQ Chat Group">
  </a>
  </div>

## 说明

- 本项目基于[nonebot2](https://github.com/nonebot/nonebot2)和[OneBot V11](https://onebot.dev/)协议，使用本插件前请先阅读以上两个项目的使用文档


##  安装及更新

<details>
<summary>第一种方式(不推荐)</summary>

- 使用`git clone https://github.com/YouthLearning/XXQG.git`指令克隆本仓库或下载压缩包文件

</details>

<details>
<summary>第二种方式(二选一)</summary>

- 使用`pip install XXQG`来进行安装,使用`pip install XXQG -U`进行更新
- 使用`nb plugin install XXQG`来进行安装,使用`nb plugin install XXQG -U`进行更新

</details>


## 导入插件

<details>
<summary>使用第一种方式安装看此方法</summary>

- 将`XXQG`放在nb的`plugins`目录下，运行nb机器人即可

- 文件结构如下

    ```py
    📦 AweSome-Bot
    ├── 📂 awesome_bot
    │   └── 📂 plugins
    |       └── 📂 XXQG
    |           └── 📜 __init__.py
    ├── 📜 .env.prod
    ├── 📜 .gitignore
    ├── 📜 pyproject.toml
    └── 📜 README.md
    ```
 


</details>

<details>
<summary>使用第二种方式安装看此方法</summary>

- 在`pyproject.toml`里的`[tool.nonebot]`中添加`plugins = ["XXQG"]`

</details>

## 机器人配置

  ```py
  HOST = "0.0.0.0"  #nonebot2监听的IP
  SUPERUSERS = [""] # 超级用户
  COMMAND_START=[""] # 命令前缀,根据需要自行修改
  local_browser_path="" # 本地浏览器程序路径 仅支持谷歌浏览器和Edge浏览器
  ```

## 功能列表
|   指令    |            指令格式             |           说明            |
|:-------:|:---------------------------:|:-----------------------:|
| 登录学习强国  |           登录学习强国            |   登录学习强国 login 添加学习强国   |
|  任务进度   |     任务进度 progress 每日任务      |        查看每日得分情况         |
|  每日答题   |          exam 每日答题          |       完成每日答题 5分/天       |
| 更新token | 更新token 刷新token updateToken |       刷新学习强国token       |
|  文章选读   |       read 每日阅读 文章选读        |     完成文章选读部分 12分/天      |
|  视听学习   |       video 每日视频 视听学习       |     完成视听学习部分 12分/天      |
|  开始学习   |       start 开始学习 每日学习       |    一键启动学习 文章 视频 答题 一共 29 分    |


## ToDo

- [ ] 优化 Bot


## 更新日志

### 2024/07/11

- 将代码上传至pypi，可使用`pip install XXQG`指令安装本插件
- 上传基础代码