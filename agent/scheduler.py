"""定时任务调度器
管理 Javis 的定时推送：早八新闻、提醒检查等。
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class TaskScheduler:
    """简单的异步定时任务调度器"""

    def __init__(self):
        self._tasks: list = []
        self._running = False

    async def start(self):
        """启动调度器"""
        self._running = True
        logger.info("定时调度器已启动")
        while self._running:
            now = datetime.now(timezone(timedelta(hours=8)))
            # 每天早上 8:00 推送新闻
            if now.hour == 8 and now.minute == 0:
                await self._push_morning_news()
                await asyncio.sleep(90)
            # 每小时检查待办截止
            if now.minute == 0:
                await self._check_deadlines()
            await asyncio.sleep(30)

    async def stop(self):
        self._running = False

    async def _push_morning_news(self):
        """推送早八新闻"""
        try:
            from api.news import fetch_daily_news
            from api.chat import ws_manager
            news = await fetch_daily_news()
            if news and "articles" in news:
                articles = news["articles"][:5]
                body = "\n".join([f"• {a['title']}" for a in articles])
                await ws_manager.broadcast("default", {
                    "type": "notification",
                    "title": f"☀️ 早间新闻 {datetime.now().strftime('%m/%d')}",
                    "body": body,
                })
                # 同时推送到 BaiLongma
                try:
                    data = json.dumps({
                        "content": f"[早间新闻] {body}",
                        "channel": "bridge"
                    }).encode()
                    import urllib.request
                    req = urllib.request.Request(
                        "http://127.0.0.1:3722/message",
                        data=data,
                        headers={"Content-Type": "application/json"},
                    )
                    urllib.request.urlopen(req, timeout=5)
                except:
                    pass
                logger.info("早八新闻已推送")
        except Exception as e:
            logger.error(f"新闻推送失败: {e}")

    async def _check_deadlines(self):
        """检查即将到期的待办"""
        try:
            from db.database import get_connection
            from api.chat import ws_manager
            conn = get_connection()
            rows = conn.execute(
                """SELECT id, title FROM todos
                   WHERE status = 'pending' AND deadline_utc IS NOT NULL
                   AND datetime(deadline_utc) <= datetime('now', '+1 hour')
                   AND datetime(deadline_utc) > datetime('now')"""
            ).fetchall()
            if rows:
                for row in rows:
                    await ws_manager.broadcast("default", {
                        "type": "notification",
                        "title": "⏰ 待办即将截止",
                        "body": f"「{row['title']}」将在 1 小时内到期",
                    })
                    await asyncio.sleep(1)
                logger.info(f"已推送 {len(rows)} 条截止提醒")
        except Exception as e:
            logger.error(f"截止检查失败: {e}")


# 全局调度器
scheduler = TaskScheduler()
