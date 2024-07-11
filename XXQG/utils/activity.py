import asyncio
import base64
import json
import os
import random
import time

from httpx import AsyncClient
from nonebot import logger
from playwright.async_api import async_playwright

from .path import DATABASE_PATH, BROWSER_DATA_PATH
from ..config import plugin_config
from ..models.user import User

tampermonkey_extension_dir = base_file_path = os.path.dirname(__file__)[:-5] + "resource"


async def getTaskProgress(token: str) -> dict:
    """
    获取当日活动列表
    :param token:
    :return:
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "Cookie": f"token={token}"
    }
    url = f"https://pc-proxy-api.xuexi.cn/delegate/score/days/listScoreProgress?sence=score&deviceType=2"
    async with AsyncClient(headers=headers) as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200 and response.json().get("code", 0) == 200:
            return {
                "status": True,
                "data": {
                    "uid": response.json()["data"]["userId"],
                    "totalScore": response.json()["data"]["totalScore"],
                    "hasRead": response.json()["data"]["taskProgress"][0]["currentScore"],
                    "maxRead": response.json()["data"]["taskProgress"][0]["dayMaxScore"],
                    "hasVideo": response.json()["data"]["taskProgress"][1]["currentScore"],
                    "maxVideo": response.json()["data"]["taskProgress"][1]["dayMaxScore"],
                    "hasLogin": response.json()["data"]["taskProgress"][2]["currentScore"],
                    "maxLogin": response.json()["data"]["taskProgress"][2]["dayMaxScore"],
                    "hasExam": response.json()["data"]["taskProgress"][-1]["currentScore"],
                    "maxExam": response.json()["data"]["taskProgress"][-1]["dayMaxScore"],
                    "status": 1 if response.json()["data"]["totalScore"] >= 30 else 0,
                }}
    return {
        "status": False
    }


async def buildAnswer(encodeStr: str) -> dict:
    """
    构造答案
    :param encodeStr:
    :return:
    """
    decodeStr = json.loads(base64.b64decode(encodeStr).decode("utf-8"))
    questions = []
    for item in decodeStr["questions"]:
        questions.append({
            "questionId": item["questionId"],
            "answers": item["correct"],
            "correct": True
        })
    return {
        "uniqueId": decodeStr["uniqueId"],
        "activityCode": "QUIZ_ALL",
        "questions": questions,
        "usedTime": random.randint(35, 80)
    }


async def todayExam(token: str) -> dict:
    """
    每日答题
    :param token:
    :return:
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "Cookie": f"token={token}"
    }
    url = "https://pc-proxy-api.xuexi.cn/api/exam/service/common/deduplicateRandomSearchV3?limit=5&activityCode=QUIZ_ALL&forced=true"
    async with AsyncClient(headers=headers) as client:
        response = await client.get(url)
        response.encoding = response.charset_encoding
        if response.status_code == 200:
            params = await buildAnswer(response.json()["data_str"])
            response = await client.post("https://pc-proxy-api.xuexi.cn/api/exam/service/practice/quizSubmitV3",
                                         json=params)
            if response.status_code == 200 and response.json().get("code", 0) == 200:
                decodeStr = json.loads(base64.b64decode(response.json()["data_str"]).decode("utf-8"))
                return {
                    "code": 200,
                    **decodeStr,
                }
        return {
            "code": 404
        }


async def getAnswer(encodeStr: str) -> list:
    decodeStr = json.loads(base64.b64decode(encodeStr).decode("utf-8"))
    dataList = []
    for i, item in enumerate(decodeStr["questions"]):
        dataList.append({
            "index": i + 1,
            "answers": item["correct"],
            "questionType": item["questionDisplay"],
            "choiceCount": len(item["answers"])
        })
    return dataList


async def todayExamByBrowser(uid: int) -> dict:
    try:
        user = await User.get(uid=uid)
        async with async_playwright() as p:
            if plugin_config.local_browser_path:
                browser = await p.chromium.launch_persistent_context(
                    user_data_dir=BROWSER_DATA_PATH,
                    executable_path=plugin_config.local_browser_path,
                    headless=True,
                    no_viewport=True,
                    viewport={"width": 1920, "height": 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                    permissions=['geolocation'],  # 仅授予地理位置权限
                    color_scheme='light',
                )
            else:
                browser = await p.chromium.launch_persistent_context(
                    user_data_dir=BROWSER_DATA_PATH,
                    headless=True,
                    no_viewport=True,
                    viewport={"width": 1920, "height": 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    locale='zh-CN',
                    timezone_id='Asia/Shanghai',
                    permissions=['geolocation'],  # 仅授予地理位置权限
                    color_scheme='light',
                )
            await browser.add_cookies([{
                "name": "token",
                "value": user.token,
                "domain": ".xuexi.cn",
                "expires": user.expires,
                "httpOnly": False,
                "path": "/"
            }])
            page = browser.pages[0]
            # 伪造 navigator 对象的一些属性
            await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {get: () => false});
                        Object.defineProperty(navigator, 'language', {get: () => 'zh-CN'});
                        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
                        Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                        """)

            # 伪造 Canvas 指纹
            await page.add_init_script("""
                        const getContext = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
                            if (contextType === '2d') {
                                const originalGetImageData = this.getImageData;
                                this.getImageData = function(sx, sy, sw, sh) {
                                    const imageData = originalGetImageData.call(this, sx, sy, sw, sh);
                                    for (let i = 0; i < imageData.data.length; i += 4) {
                                        imageData.data[i] += 1; // 伪造 Canvas 数据
                                    }
                                    return imageData;
                                };
                            }
                            return getContext.call(this, contextType, ...args);
                        };
                        """)

            # 伪造 WebGL 指纹
            await page.add_init_script("""
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            if (parameter === 37446) {
                                return 'Intel Inc.'; // 伪造 GPU 厂商
                            }
                            if (parameter === 37447) {
                                return 'Intel Iris OpenGL Engine'; // 伪造 GPU 渲染器
                            }
                            return getParameter.call(this, parameter);
                        };
                        """)
            target_url = "https://pc-proxy-api.xuexi.cn/api/exam/service/common/deduplicateRandomSearchV3?limit=5&activityCode=QUIZ_ALL&forced=true"  # 替换为你要监听的 GET 请求的 URL

            # 监听响应事件
            async def handle_response(response):
                if response.request.url == target_url and response.request.method == "GET":
                    # 获取并打印响应的文本内容
                    body = await response.json()
                    answerList = await getAnswer(body['data_str'])
                    with open(DATABASE_PATH / f'answer_{uid}.json', "w", encoding="utf-8") as w:
                        json.dump(answerList, w, indent=4, ensure_ascii=False)
                elif response.request.url == "https://pc-proxy-api.xuexi.cn/api/exam/service/practice/quizSubmitV3" and response.request.method == "POST":
                    body = await response.json()
                    decodeStr = json.loads(base64.b64decode(body["data_str"]).decode("utf-8"))
                    with open(DATABASE_PATH / f'score_{uid}.json', "w", encoding="utf-8") as w:
                        json.dump(decodeStr, w, indent=4, ensure_ascii=False)

            page.on("response", handle_response)
            await page.goto("https://www.xuexi.cn/")
            # 等待导航完成
            await page.wait_for_load_state('networkidle')
            await page.goto("https://pc.xuexi.cn/points/my-study.html")
            # 等待导航完成
            await page.wait_for_load_state('networkidle')
            await page.goto("https://pc.xuexi.cn/points/exam-index.html")

            # 等待导航完成
            await page.wait_for_load_state('networkidle')
            # await page.locator("#app > div > div.layout-body > div > div.blocks > div:nth-child(1)").click()
            await page.goto("https://pc.xuexi.cn/points/exam-practice.html")
            # 等待导航完成
            await page.wait_for_load_state('networkidle')
            # 读取答案
            with open(DATABASE_PATH / f'answer_{uid}.json', "r", encoding="utf-8") as r:
                answerList = json.load(r)
            for item in answerList:
                await page.locator(".q-footer .tips").click()
                await asyncio.sleep(random.random() * 2)
                await page.locator(".q-footer .tips").click()
                if item["questionType"] == 4:
                    # 等待文本输入框区域加载完成
                    textInputs = await page.locator(".q-body input").element_handles()
                    for i, textInput in enumerate(textInputs):
                        await textInput.fill(item["answers"][i]["value"])
                else:
                    # 等待答案选项区域加载完成
                    await page.locator(".q-answer").first.wait_for()
                    answers = await page.locator(".q-answer").element_handles()
                    for item2 in item["answers"]:
                        for answer in answers:
                            text_content = await answer.text_content()
                            logger.opt(colors=True).debug(f"答题选项：{text_content}")
                            if item2["value"] in text_content:
                                await answer.click()
                                await asyncio.sleep(random.random() * 3)
                                break  # 找到并点击后跳出内层循环
                # 等待并点击提交按钮
                btn = await page.locator(".ant-btn.next-btn").first.click()
                # 等待页面刷新并加载新问题
                await page.wait_for_selector(".detail-body .question")
                # 添加一个延迟，确保页面完成重新加载
                await asyncio.sleep(random.random() * 5)
            logger.opt(colors=True).debug("检测是否存在滑块验证码~")
            verifyCode = await handle_slide_verify(page)
            await asyncio.sleep(random.randint(1, 3))
            btn = await page.locator(".ant-btn span").text_content()
            if btn.strip() == "再来一组":
                with open(DATABASE_PATH / f'score_{uid}.json', "r", encoding="utf-8") as r:
                    data = json.load(r)
                return {
                    "status": True,
                    **data
                }
            if verifyCode == 403:
                return {
                    "status": False,
                    "msg": "验证失败！"
                }
            elif verifyCode == 200:
                with open(DATABASE_PATH / f'score_{uid}.json', "r", encoding="utf-8") as r:
                    data = json.load(r)
                return {
                    "status": True,
                    **data
                }
            else:
                with open(DATABASE_PATH / f'score_{uid}.json', "r", encoding="utf-8") as r:
                    data = json.load(r)
                return {
                    "status": True,
                    **data
                }
    except Exception as e:
        logger.opt(colors=True).error(e)
        return {
            "status": False,
            "msg": e
        }


async def getArticles() -> list:
    """
    获取最新15条新闻列表
    :return:
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
    }
    articles = []
    urls = [
        'https://www.xuexi.cn/lgdata/35il6fpn0ohq.json',
        'https://www.xuexi.cn/lgdata/1ap1igfgdn2.json',
        'https://www.xuexi.cn/lgdata/vdppiu92n1.json',
        'https://www.xuexi.cn/lgdata/152mdtl3qn1.json',
    ]
    async with AsyncClient(headers=headers) as client:
        for url in urls:
            response = await client.get(url)
            articles += response.json()[:10]
    sorted_articles = sorted(articles, key=lambda x: x['publishTime'], reverse=True)
    return sorted_articles[:15]


async def getVideos() -> list:
    """
    获取最新15条新闻视频
    :return:
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"
    }
    videos = []
    urls = [
        'https://www.xuexi.cn/lgdata/525pi8vcj24p.json',
        'https://www.xuexi.cn/lgdata/11vku6vt6rgom.json',
        'https://www.xuexi.cn/lgdata/2qfjjjrprmdh.json',
        'https://www.xuexi.cn/lgdata/3o3ufqgl8rsn.json',
        'https://www.xuexi.cn/lgdata/591ht3bc22pi.json',
        'https://www.xuexi.cn/lgdata/1742g60067k.json',
        'https://www.xuexi.cn/lgdata/1novbsbi47k.json',
    ]
    async with AsyncClient(headers=headers) as client:
        for url in urls:
            response = await client.get(url)
            videos += response.json()[:10]
    sorted_videos = sorted(videos, key=lambda x: x['publishTime'], reverse=True)
    return sorted_videos[:15]


async def readArticle(uid: int):
    """
    阅读文章
    :param uid:
    :return:
    """
    user = await User.get(uid=uid)
    nowTime = time.time()
    articles = await getArticles()
    async with async_playwright() as p:
        if plugin_config.local_browser_path:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_PATH,
                executable_path=plugin_config.local_browser_path,
                headless=True,
                no_viewport=True,
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['geolocation'],  # 仅授予地理位置权限
                color_scheme='light',
            )
        else:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_PATH,
                headless=True,
                no_viewport=True,
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['geolocation'],  # 仅授予地理位置权限
                color_scheme='light',
            )
        await browser.add_cookies([{
            "name": "token",
            "value": user.token,
            "domain": ".xuexi.cn",
            "expires": user.expires,
            "httpOnly": False,
            "path": "/"
        }])
        page = browser.pages[0]
        # 伪造 navigator 对象的一些属性
        await page.add_init_script("""
                            Object.defineProperty(navigator, 'webdriver', {get: () => false});
                            Object.defineProperty(navigator, 'language', {get: () => 'zh-CN'});
                            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
                            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                            """)
        # 伪造 Canvas 指纹
        await page.add_init_script("""
                            const getContext = HTMLCanvasElement.prototype.getContext;
                            HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
                                if (contextType === '2d') {
                                    const originalGetImageData = this.getImageData;
                                    this.getImageData = function(sx, sy, sw, sh) {
                                        const imageData = originalGetImageData.call(this, sx, sy, sw, sh);
                                        for (let i = 0; i < imageData.data.length; i += 4) {
                                            imageData.data[i] += 1; // 伪造 Canvas 数据
                                        }
                                        return imageData;
                                    };
                                }
                                return getContext.call(this, contextType, ...args);
                            };
                            """)
        # 伪造 WebGL 指纹
        await page.add_init_script("""
                            const getParameter = WebGLRenderingContext.prototype.getParameter;
                            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                                if (parameter === 37446) {
                                    return 'Intel Inc.'; // 伪造 GPU 厂商
                                }
                                if (parameter === 37447) {
                                    return 'Intel Iris OpenGL Engine'; // 伪造 GPU 渲染器
                                }
                                return getParameter.call(this, parameter);
                            };
                            """)
        await page.goto("https://www.xuexi.cn")
        await page.wait_for_load_state('networkidle')
        for i, item in enumerate(articles):
            try:
                startScoreData = await getTaskProgress(user.token)
                startScore = 0
                if startScoreData["status"]:
                    startScore = startScoreData["data"]["hasRead"]
                logger.opt(colors=True).debug(f"开始加载第{i + 1}篇文章：{item['url']}")
                await page.goto(item["url"])
                await page.wait_for_load_state('networkidle')
                logger.opt(colors=True).debug(f"第{i + 1}篇文章加载完成~")
                sections = await page.query_selector_all('section')
                max_text_count = max(
                    [await page.evaluate('(section) => section.innerText.length', s) for s in sections],
                    default=200)

                async def scroll_page():
                    await page.evaluate('window.scrollTo(0, 400)')
                    await page.mouse.wheel(0, 400)
                    await page.mouse.move(100, 100)
                    await page.click('body')

                await scroll_page()
                readStatus = True
                while readStatus:
                    if (time.time() - nowTime) > 140:
                        break
                    scoreData = await getTaskProgress(user.token)
                    score = 0
                    if scoreData["status"]:
                        score = scoreData["data"]["hasRead"]
                        if scoreData["data"]["hasRead"] == scoreData["data"]["maxRead"]:
                            return
                    if (score - startScore) >= 2:
                        break
                    await asyncio.sleep(random.randint(5, 15))
            except Exception as e:
                logger.opt(colors=True).error(e)


async def readVideo(uid: int):
    """
    阅读视频
    :param uid:
    :return:
    """
    user = await User.get(uid=uid)
    nowTime = time.time()
    videos = await getVideos()
    async with async_playwright() as p:
        if plugin_config.local_browser_path:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_PATH,
                executable_path=plugin_config.local_browser_path,
                headless=True,
                no_viewport=True,
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['geolocation'],  # 仅授予地理位置权限
                color_scheme='light',
            )
        else:
            browser = await p.firefox.launch_persistent_context(
                user_data_dir=BROWSER_DATA_PATH,
                headless=True,
                no_viewport=True,
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0 ',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['geolocation'],  # 仅授予地理位置权限
                color_scheme='light',
            )
        await browser.add_cookies([{
            "name": "token",
            "value": user.token,
            "domain": ".xuexi.cn",
            "expires": user.expires,
            "httpOnly": False,
            "path": "/"
        }])
        page = browser.pages[0]
        # 伪造 navigator 对象的一些属性
        await page.add_init_script("""
                            Object.defineProperty(navigator, 'webdriver', {get: () => false});
                            Object.defineProperty(navigator, 'language', {get: () => 'zh-CN'});
                            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
                            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                            """)
        # 伪造 Canvas 指纹
        await page.add_init_script("""
                            const getContext = HTMLCanvasElement.prototype.getContext;
                            HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
                                if (contextType === '2d') {
                                    const originalGetImageData = this.getImageData;
                                    this.getImageData = function(sx, sy, sw, sh) {
                                        const imageData = originalGetImageData.call(this, sx, sy, sw, sh);
                                        for (let i = 0; i < imageData.data.length; i += 4) {
                                            imageData.data[i] += 1; // 伪造 Canvas 数据
                                        }
                                        return imageData;
                                    };
                                }
                                return getContext.call(this, contextType, ...args);
                            };
                            """)
        # 伪造 WebGL 指纹
        await page.add_init_script("""
                            const getParameter = WebGLRenderingContext.prototype.getParameter;
                            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                                if (parameter === 37446) {
                                    return 'Intel Inc.'; // 伪造 GPU 厂商
                                }
                                if (parameter === 37447) {
                                    return 'Intel Iris OpenGL Engine'; // 伪造 GPU 渲染器
                                }
                                return getParameter.call(this, parameter);
                            };
                            """)
        await page.goto("https://www.xuexi.cn/")
        await page.wait_for_load_state('networkidle')
        for i, item in enumerate(videos):
            try:
                startScoreData = await getTaskProgress(user.token)
                startScore = 0
                if startScoreData["status"]:
                    startScore = startScoreData["data"]["hasRead"]
                logger.opt(colors=True).debug(f"开始加载第{i + 1}个视频：{item['url']}")
                await page.goto(item["url"])
                await page.wait_for_load_state('networkidle')
                logger.opt(colors=True).debug(f"第{i + 1}个视频加载完成~")
                await page.goto(item["url"])
                await page.wait_for_load_state('networkidle')
                # 尝试播放视频
                try:
                    await page.evaluate("document.querySelector('video').play()")
                    logger.opt(colors=True).debug("视频开始播放")
                except Exception as e:
                    logger.opt(colors=True).error(f"播放视频时出错: {e}")
                    return False
                readStatus = True
                while readStatus:
                    if (time.time() - nowTime) > 140:
                        break
                    scoreData = await getTaskProgress(user.token)
                    score = 0
                    if scoreData["status"]:
                        score = scoreData["data"]["hasVideo"]
                        if scoreData["data"]["hasVideo"] == scoreData["data"]["maxVideo"]:
                            return
                    if (score - startScore) >= 2:
                        break
                    await asyncio.sleep(random.randint(5, 15))
            except Exception as e:
                logger.opt(colors=True).error(e)


async def handle_slide_verify(page):
    mask = await page.query_selector('#nc_mask')
    if mask and await mask.is_visible():
        logger.opt(colors=True).debug("等待滑动验证")
        await asyncio.sleep(random.random() * 5)
        await mask.evaluate("element => element.style.zIndex = '999'")
        track = await page.query_selector('.nc_scale')
        slide = await page.query_selector('.btn_slide')
        rect_track = await track.bounding_box()
        rect_slide = await slide.bounding_box()
        start_x = rect_slide['x'] + rect_slide['width'] / 2
        start_y = rect_slide['y'] + rect_slide['height'] / 2
        end_x = rect_track['x'] + rect_track['width'] - rect_slide['width'] / 2
        end_y = start_y

        def create_random_path(start, end, steps):
            path = []
            for i in range(steps):
                x = start['x'] + (end['x'] - start['x']) * (i / steps)
                y = start['y'] + (end['y'] - start['y']) * (i / steps)
                path.append({'x': x, 'y': y})
            path.append(end)
            return path

        start_point = {'x': start_x, 'y': start_y}
        end_point = {'x': end_x, 'y': end_y}
        path = create_random_path(start_point, end_point, 10)
        # 模拟滑动
        await page.mouse.move(start_point['x'], start_point['y'])
        await page.mouse.down()
        for point in path:
            await page.mouse.move(point['x'], point['y'], steps=5)
            await asyncio.sleep(0.01)
        await page.mouse.up()
        logger.opt(colors=True).debug("滑动验证完成!")
        await page.wait_for_load_state('networkidle')
        logger.opt(colors=True).debug("验证滑动是否成功~")
        btn = await page.locator(".ant-btn span").text_content()
        if btn == "再来一组":
            logger.opt(colors=True).debug("滑动验证失败!")
            return 403
        else:
            logger.opt(colors=True).debug("滑动验证成功!")
            return 200
    else:
        logger.opt(colors=True).debug("滑动验证未显示")
        return 404


async def handle_new_window(context):
    # 监听新窗口事件
    new_page = await context.wait_for_event('page')
    return new_page


async def startTask(uid: int):
    user = await User.get(uid=uid)
    # 启动Edge浏览器，并加载油猴扩展
    async with async_playwright() as p:
        if plugin_config.local_browser_path:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_PATH,
                executable_path=plugin_config.local_browser_path,
                headless=False,
                no_viewport=True,
                args=[
                    f'--disable-extensions-except={tampermonkey_extension_dir}',
                    f'--load-extension={tampermonkey_extension_dir}'
                ],
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['geolocation'],  # 仅授予地理位置权限
                color_scheme='light',
            )
        else:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_DATA_PATH,
                headless=True,
                no_viewport=True,
                args=[
                    f'--disable-extensions-except={tampermonkey_extension_dir}',
                    f'--load-extension={tampermonkey_extension_dir}'
                ],
                viewport={"width": 1920, "height": 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['geolocation'],  # 仅授予地理位置权限
                color_scheme='light',
            )
        await browser.add_cookies([{
            "name": "token",
            "value": user.token,
            "domain": ".xuexi.cn",
            "expires": user.expires,
            "httpOnly": False,
            "path": "/"
        }])
        page = browser.pages[0]
        # 伪造 navigator 对象的一些属性
        await page.add_init_script("""
                            Object.defineProperty(navigator, 'webdriver', {get: () => false});
                            Object.defineProperty(navigator, 'language', {get: () => 'zh-CN'});
                            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
                            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
                            """)
        # 伪造 Canvas 指纹
        await page.add_init_script("""
                            const getContext = HTMLCanvasElement.prototype.getContext;
                            HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
                                if (contextType === '2d') {
                                    const originalGetImageData = this.getImageData;
                                    this.getImageData = function(sx, sy, sw, sh) {
                                        const imageData = originalGetImageData.call(this, sx, sy, sw, sh);
                                        for (let i = 0; i < imageData.data.length; i += 4) {
                                            imageData.data[i] += 1; // 伪造 Canvas 数据
                                        }
                                        return imageData;
                                    };
                                }
                                return getContext.call(this, contextType, ...args);
                            };
                            """)
        # 伪造 WebGL 指纹
        await page.add_init_script("""
                            const getParameter = WebGLRenderingContext.prototype.getParameter;
                            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                                if (parameter === 37446) {
                                    return 'Intel Inc.'; // 伪造 GPU 厂商
                                }
                                if (parameter === 37447) {
                                    return 'Intel Iris OpenGL Engine'; // 伪造 GPU 渲染器
                                }
                                return getParameter.call(this, parameter);
                            };
                            """)
        # 等待Edge浏览器加载完成
        await page.goto('https://www.xuexi.cn')
        new_page = await handle_new_window(browser)
        await new_page.locator(".egg_study_btn").click()
        while True:
            startScoreData = await getTaskProgress(user.token)
            if startScoreData["data"]["hasRead"] == startScoreData["data"]["maxRead"] and startScoreData["data"][
                "hasVideo"] == startScoreData["data"]["maxVideo"]:
                return {
                    "status": True
                }
            await asyncio.sleep(random.randint(10, 15))
