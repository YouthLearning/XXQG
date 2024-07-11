import asyncio
import datetime
import time

from nonebot import get_driver, require, get_bot
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment, Bot, GROUP
from nonebot.rule import Rule
from nonebot.permission import SUPERUSER

from .activity import getTaskProgress, todayExam, readArticle, readVideo, todayExamByBrowser, startTask
from .login import getQrCode, getQrcodeStatus, getLogin, getUserInfo, getUserScore, updateToken
from .rule import must_command
from ..models.log import Log
from ..models.user import User, TodayScore

SUPERS = get_driver().config.superusers
scheduler = require('nonebot_plugin_apscheduler').scheduler
login = on_command("login", aliases={"登录学习强国", "添加学习强国"}, permission=SUPERUSER | GROUP, priority=50,rule=Rule(must_command))
progress = on_command("progress", aliases={"任务进度", "每日任务"}, permission=SUPERUSER | GROUP, priority=50,rule=Rule(must_command))
exam = on_command("exam", aliases={"每日答题"}, permission=SUPERUSER | GROUP, priority=50,rule=Rule(must_command))
updatetoken = on_command("updateToken", aliases={"更新token", "刷新token"}, permission=SUPERUSER | GROUP, priority=50,rule=Rule(must_command))
read = on_command("read", aliases={"每日阅读", "文章选读"}, permission=SUPERUSER | GROUP, priority=50,rule=Rule(must_command))
video = on_command("video", aliases={"每日视频", "视听学习"}, permission=SUPERUSER | GROUP, priority=50,rule=Rule(must_command))
start = on_command("start", aliases={"开始学习", "每日学习"}, priority=50, permission=SUPERUSER | GROUP,rule=Rule(must_command))


@login.handle()
async def login_(event: GroupMessageEvent) -> None:
    qrCodeData = await getQrCode()
    if qrCodeData["status"]:
        await login.send(
            message=MessageSegment.text(
                f"请使用学习强国APP扫码登录，两分钟内有效~\n也可点击链接查看登录二维码：{qrCodeData['code_url']}\n") + MessageSegment.image(
                qrCodeData["content"]), at_sender=True)
        qrCodeStatus = False
        now_time = time.time()
        while not qrCodeStatus:
            if (time.time() - now_time) > 120:
                await login.finish(message=MessageSegment.text("二维码过期，请重新发指令 登录学习强国 进行登录~"),
                                   at_sender=True)
                break
            qrCodeStatusData = await getQrcodeStatus(qrCodeData["qrcode"])
            await asyncio.sleep(2)
            if qrCodeStatusData["success"]:
                qrCodeStatus = True
                loginTmpCode = qrCodeStatusData["data"].split("=")[-1]
                loginData = await getLogin(code=loginTmpCode)
                if loginData["status"]:
                    userInfo = {
                        "token": loginData["content"],
                        "expires": time.time() + 60 * 60 * 6
                    }
                    userInfoData = await getUserInfo(loginData["content"])
                    if userInfoData["status"]:
                        userInfo.update(userInfoData["data"])
                    else:
                        await login.finish(
                            message=MessageSegment.text("登录失败~，请重新发指令 登录学习强国 进行登录~"),
                            at_sender=True)
                        break
                    userScoreData = await getUserScore(loginData["content"])
                    if userScoreData["status"]:
                        userInfo.update({"score": userScoreData["score"]})
                    user = await User.get_or_none(userId=event.user_id)
                    if user:
                        await User.filter(id=user.id).update(**userInfo)
                    else:
                        await User.create(
                            userId=event.user_id,
                            groupId=event.group_id,
                            **userInfo
                        )
                    await login.finish(message=MessageSegment.text("登陆成功~"),
                                       at_sender=True)


@progress.handle()
async def getInfo(event: GroupMessageEvent) -> None:
    user = await User.get_or_none(userId=event.user_id)
    if user:
        taskInfoData = await getTaskProgress(user.token)
        if taskInfoData["status"]:
            message = f"""\n昵称：{user.nickname}\nuid：{taskInfoData['data']['uid']}\n当天积分：{taskInfoData['data']['totalScore']}/30\n每日登录：{taskInfoData['data']['hasLogin']}/{taskInfoData['data']['maxLogin']}\n文章选读：{taskInfoData['data']['hasRead']}/{taskInfoData['data']['maxRead']}\n视听学习：{taskInfoData['data']['hasVideo']}/{taskInfoData['data']['maxVideo']}\n每日答题：{taskInfoData['data']['hasExam']}/{taskInfoData['data']['maxExam']}\n查询时间：{datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}"""
            taskInfoData["data"].pop("uid")
            todayScore = await TodayScore.get_or_none(user=user.id)
            if todayScore:
                await TodayScore.filter(user=user.id).update(**taskInfoData["data"])
            else:
                await TodayScore.create(user=user, **taskInfoData["data"])
            await progress.finish(message=MessageSegment.text(message), at_sender=True)
        else:
            await progress.finish(message=MessageSegment.text("数据拉取失败~，请稍后重试~"))
    await progress.finish(message=MessageSegment.text("您还没有绑定~，请发指令 添加学习强国 进行绑定~"), at_sender=True)


@exam.handle()
async def todayExam_(event: GroupMessageEvent) -> None:
    user = await User.get_or_none(userId=event.user_id)
    if user:
        taskLog = await Log.filter(user=user.id, status=0, type=4)
        if taskLog:
            await exam.finish(message=MessageSegment.text("答题失败，您有答题任务等待执行中~"),
                              at_sender=True)
        await exam.send(message=MessageSegment.text("正在答题中，请稍后~"), at_sender=True)
        examInfoData = await todayExam(user.token)
        if examInfoData["code"] == 200:
            await Log.filter(user=user.id, type=4).update(status=1)
            await Log.filter(user=user.id, status=0, type=4).update(status=1, score=examInfoData['correctNum'])
            await exam.finish(message=MessageSegment.text(
                f"\n每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"),
                at_sender=True)
        else:
            examInfoData = await todayExamByBrowser(user.uid)
            if examInfoData["status"]:
                await Log.filter(user=user.id, type=4).update(status=1)
                await Log.filter(user=user.id, status=0, type=4).update(status=1, score=examInfoData['correctNum'])
                await exam.finish(message=MessageSegment.text(
                    f"\n每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"),
                    at_sender=True)
            else:
                await exam.finish(message=MessageSegment.text("每日答题失败，请稍后重试！"), at_sender=True)
    await exam.finish(message=MessageSegment.text("您还没有绑定~，请发指令 添加学习强国 进行绑定~"), at_sender=True)


@updatetoken.handle()
async def update_token(event: GroupMessageEvent) -> None:
    user = await User.get_or_none(userId=str(event.user_id))
    if user:
        status = await updateToken(user.uid)
        if status:
            await updatetoken.finish(message=MessageSegment.text("Token更新成功！"), at_sender=True)
        await updatetoken.finish(message=MessageSegment.text("Token更新失败！"), at_sender=True)
    await updatetoken.finish(message=MessageSegment.text("您还没有绑定~，请发指令 添加学习强国 进行绑定~"),
                             at_sender=True)


@read.handle()
async def read_(event: GroupMessageEvent) -> None:
    user = await User.get_or_none(userId=str(event.user_id))
    if user:
        startScoreData = await getTaskProgress(user.token)
        if startScoreData["status"]:
            if startScoreData["data"]["hasRead"] == startScoreData["data"]["maxRead"]:
                await Log.filter(user=user.id, type=2).update(status=1)
                await read.finish(message=MessageSegment.text("文章选读已完成~"), at_sender=True)
        await read.send(message=MessageSegment.text("正在文章选读中，请稍等，预计花费15分钟~"), at_sender=True)
        await readArticle(user.uid)
        while True:
            scoreData = await getTaskProgress(user.token)
            if scoreData["status"]:
                if scoreData["data"]["hasRead"] == scoreData["data"]["maxRead"]:
                    await Log.filter(user=user.id, type=2).update(status=1)
                    await read.finish(message=MessageSegment.text("文章选读已完成~"), at_sender=True)
                else:
                    await read.finish(message=MessageSegment.text("文章选读失败，请稍后重试~"), at_sender=True)
    else:
        await read.finish(message=MessageSegment.text("您还没有绑定~，请发指令 添加学习强国 进行绑定~"),
                          at_sender=True)


@video.handle()
async def video_(event: GroupMessageEvent) -> None:
    user = await User.get_or_none(userId=str(event.user_id))
    if user:
        startScoreData = await getTaskProgress(user.token)
        if startScoreData["status"]:
            if startScoreData["data"]["hasVideo"] == startScoreData["data"]["maxVideo"]:
                await Log.filter(user=user.id, type=3).update(status=1)
                await video.finish(message=MessageSegment.text("视听学习已完成~"), at_sender=True)
        await video.send(message=MessageSegment.text("正在视听学习中，请稍等，预计花费15分钟~"), at_sender=True)
        await readVideo(user.uid)
        while True:
            scoreData = await getTaskProgress(user.token)
            if scoreData["status"]:
                if scoreData["data"]["hasVideo"] == scoreData["data"]["maxVideo"]:
                    await Log.filter(user=user.id, type=3).update(status=1)
                    await video.finish(message=MessageSegment.text("视听学习已完成~"), at_sender=True)
                else:
                    await video.finish(message=MessageSegment.text("视听学习失败，请稍后重试~"), at_sender=True)
    else:
        await video.finish(message=MessageSegment.text("您还没有绑定~，请发指令 添加学习强国 进行绑定~"),
                           at_sender=True)


@start.handle()
async def startStudy(event: GroupMessageEvent) -> None:
    user = await User.get_or_none(userId=str(event.user_id))
    if user:
        startScoreData = await getTaskProgress(user.token)
        if startScoreData["data"]["hasRead"] == startScoreData["data"]["maxRead"] and startScoreData["data"][
            "hasVideo"] == startScoreData["data"]["maxVideo"]:
            await start.send(message="文章选读和视频视听完毕，开始每日答题~", at_sender=True)
            await Log.filter(user=user.id, type=2).update(status=1)
            await Log.filter(user=user.id, type=3).update(status=1)
            examInfoData = await todayExam(user.token)
            if examInfoData["code"] == 200:
                await Log.filter(user=user.id, type=4).update(status=1)
                await start.finish(message=MessageSegment.text(
                    f"\n每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"),
                    at_sender=True)
            else:
                examInfoData = await todayExamByBrowser(user.uid)
                if examInfoData["status"]:
                    await Log.filter(user=user.id, type=4).update(status=1)
                    await start.finish(message=MessageSegment.text(
                        f"\n每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"),
                        at_sender=True)
                else:
                    await start.finish(message=MessageSegment.text("每日答题失败！"), at_sender=True)
        await start.send(message=MessageSegment.text("开始文章选读和视频视听中，请稍等~"), at_sender=True)
        status = await startTask(user.uid)
        if status["status"]:
            await start.send(message="文章选读和视频视听完毕，开始每日答题~", at_sender=True)
            examInfoData = await todayExam(user.token)
            if examInfoData["code"] == 200:
                await start.finish(message=MessageSegment.text(
                    f"\n每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"),
                    at_sender=True)
            else:
                examInfoData = await todayExamByBrowser(user.uid)
                if examInfoData["status"]:
                    await start.finish(message=MessageSegment.text(
                        f"\n每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"),
                        at_sender=True)
                else:
                    await start.finish(message=MessageSegment.text("每日答题失败！"), at_sender=True)


@scheduler.scheduled_job('cron', day_of_week='0-6', hour="*/2", id='update_token', timezone="Asia/Shanghai")
async def update_token():
    users = await User.filter(status=1).values()
    for item in users:
        await updateToken(item["uid"])


@scheduler.scheduled_job('cron', day_of_week='0-6', hour="0", id='update_task', timezone="Asia/Shanghai")
async def update_task():
    users = await User.filter(status=1, auto=True).values()
    for i, item in enumerate(users):
        user = await User.get_or_none(id=item["id"])
        await Log.create(
            type=2,
            index=i+1,
            user=user,
            status=0
        )
        await Log.create(
            type=3,
            index=i+1,
            user=user,
            status=0
        )
        await Log.create(
            type=4,
            index=i+1,
            user=user,
            status=0
        )
        await updateToken(item["uid"])


@scheduler.scheduled_job('cron', day_of_week='0-6', hour="0", id='start_study', timezone="Asia/Shanghai")
async def start_study():
    try:
        bot: Bot = get_bot()
    except ValueError as e:
        logger.opt(colors=True).error(e)
        return
    users = await User.filter(status=1, auto=True).values()
    for item in users:
        user = await User.get(id=item["id"])
        startScoreData = await getTaskProgress(user.token)
        if startScoreData["data"]["hasRead"] == startScoreData["data"]["maxRead"] and startScoreData["data"][
            "hasVideo"] == startScoreData["data"]["maxVideo"]:
            await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                               message=MessageSegment.at(user.userId) + MessageSegment.text(
                                   "自动文章选读和视频视听完毕，开始每日答题~"))
            await Log.filter(user=user.id, type=2).update(status=1)
            await Log.filter(user=user.id, type=3).update(status=1)
            examInfoData = await todayExam(user.token)
            if examInfoData["code"] == 200:
                await Log.filter(user=user.id, type=4).update(status=1)
                await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                                   message=MessageSegment.at(user.userId) + MessageSegment.text(
                                       f"\n自动每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"))
                continue
            else:
                examInfoData = await todayExamByBrowser(user.uid)
                if examInfoData["status"]:
                    await Log.filter(user=user.id, type=4).update(status=1)
                    await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                                       message=MessageSegment.at(user.userId) + MessageSegment.text(
                                           f"\n自动每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"))
                    continue
                else:
                    await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                                       message=MessageSegment.at(user.userId) + MessageSegment.text("自动每日答题失败！"))
                    continue
        await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                            message=MessageSegment.at(user.userId) + MessageSegment.text(
                                "自动开始文章选读和视频视听中，请稍等~"))
        status = await startTask(user.uid)
        if status["status"]:
            await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                               message=MessageSegment.at(user.userId) + MessageSegment.text(
                                   "自动文章选读和视频视听完毕，开始每日答题~"))
            examInfoData = await todayExam(user.token)
            if examInfoData["code"] == 200:
                await Log.filter(user=user.id, type=4).update(status=1)
                await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                                   message=MessageSegment.at(user.userId) + MessageSegment.text(
                                       f"\n自动每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"))
                continue
            else:
                examInfoData = await todayExamByBrowser(user.uid)
                if examInfoData["status"]:
                    await Log.filter(user=user.id, type=4).update(status=1)
                    await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                                       message=MessageSegment.at(user.userId) + MessageSegment.text(
                                           f"\n自动每日答题成功！\n昵称：{user.nickname}\nuid：{user.uid}\n正确率：{examInfoData['correctRate']}\n答对题数：{examInfoData['correctNum']}\n错题数：{examInfoData['wrongNum']}\n答题时间：{examInfoData['usedTime']}\n答题时间：{datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"))
                    continue
                else:
                    await bot.send_msg(message_type="group", user_id=user.userId, group_id=user.groupId,
                                       message=MessageSegment.at(user.userId) + MessageSegment.text("自动每日答题失败！"))
                    continue
