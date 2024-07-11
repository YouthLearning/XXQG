import base64
import time
import uuid
from io import BytesIO

from httpx import AsyncClient

from src.plugins.XXQG.models.user import User


async def getQrCode():
    """
    获取二维码
    :return:
    """
    headers = {
        "Referer": "https://api.qrserver.com/",
    }
    try:
        async with AsyncClient(headers=headers) as client:
            response = await client.get("https://login.xuexi.cn/user/qrcode/generate")
            if response.status_code == 200 and response.json().get("success", False):
                result = response.json()["result"]
                code_url = f"https://api.qrserver.com/v1/create-qr-code/?data=https://login.xuexi.cn/login/qrcommit?code={result}&appId=dingoankubyrfkttorhpou"
                response = await client.get(code_url)
                buf = BytesIO(response.content)
                base64_str = base64.b64encode(buf.getbuffer()).decode()
                content = "base64://" + base64_str
                return {
                    "status": True,
                    "code_url": code_url,
                    "content": content,
                    "qrcode": result
                }
    except Exception as e:
        return {
            "status": False,
        }


async def getQrcodeStatus(qrCode: str):
    """
    获取二维码状态
    :param qrCode:
    :return:
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
    }
    params = {
        "qrCode": qrCode,
        "goto": "https://oa.xuexi.cn",
        "pdmToken": ""
    }
    async with AsyncClient(headers=headers) as client:
        response = await client.post("https://login.xuexi.cn/login/login_with_qr", params=params)
        if response.status_code == 200 and response.json().get("success", False):
            return response.json()
        return {
            "data": "",
            "success": False
        }


async def getSign():
    """获取签名"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    }
    async with AsyncClient(headers=headers) as client:
        response = await client.get("https://pc-api.xuexi.cn/open/api/sns/sign")
        if response.status_code == 200 and response.json().get("code", 0) == 200:
            return response.json()["data"]["sign"]
        return ""


async def getLogin(code: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    }
    url = f"https://pc-api.xuexi.cn/login/secure_check?code={code}&state={await getSign() + uuid.uuid4().__str__()}"
    async with AsyncClient(headers=headers) as client:
        response = await client.get(url)
        if response.status_code == 200 and response.json().get("success", False):
            set_cookie_headers = response.headers.get_list('set-cookie')
            for header in set_cookie_headers:
                parts = header.split(';')
                for part in parts:
                    key_value = part.strip().split('=', 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        if key == "token" or key == "TOKEN":
                            return {
                                "status": True,
                                "content": value
                            }
        return {
            "status": False
        }


async def getUserInfo(token: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "Cookie": f"token={token}"
    }
    async with AsyncClient(headers=headers) as client:
        response = await client.get("https://pc-api.xuexi.cn/open/api/user/info")
        if response.json().get("code", 0) == 200 and response.status_code == 200:
            return {
                "status": True,
                "data": {
                    "uid": response.json()["data"]["uid"],
                    "nickname": response.json()["data"]["nick"],
                    "avatar": response.json()["data"]["avatarMediaUrl"]
                }}
    return {
        "status": False
    }


async def getUserScore(token: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "Cookie": f"token={token}"
    }
    async with AsyncClient(headers=headers) as client:
        response = await client.get("https://pc-proxy-api.xuexi.cn/delegate/score/get")
        if response.json().get("code", 0) == 200 and response.status_code == 200:
            return {
                "status": True,
                "score": response.json()["data"]["score"]}
    return {
        "status": False
    }


async def updateToken(uid: int) -> bool:
    user = await User.get(uid=uid)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
        "Cookie": f"token={user.token}"
    }
    async with AsyncClient(headers=headers) as client:
        response = await client.get("https://pc-api.xuexi.cn/open/api/auth/check")
        if response.status_code == 200 and response.json().get("code", 0)==200:
            set_cookie_headers = response.headers.get_list('set-cookie')
            for header in set_cookie_headers:
                parts = header.split(';')
                for part in parts:
                    key_value = part.strip().split('=', 1)
                    if len(key_value) == 2:
                        key, value = key_value
                        if key == "token" or key == "TOKEN":
                            await User.filter(id=user.id).update(
                                token=value,
                                expires=time.time() + 60 * 60 * 4
                            )
                            return True
        return False
