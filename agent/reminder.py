"""提醒引擎
定时扫描待办与提醒列表，到期时推送通知给用户。
运行在后台线程，通过 WebSocket 推送或回调通知用户。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from db.database import get_connection

logger = logging.getLogger(__name__)


class ReminderEngine:
    """提醒引擎，定时检查到期待办并触发推送"""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._push_callback: Optional[Callable] = None
        self._check_interval = 30  # 每 30 秒扫描一次

    def set_push_callback(self, callback: Callable):
        """设置推送回调函数，接收提醒内容"""
        self._push_callback = callback

    async def start(self):
        """启动提醒引擎（后台任务）"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("提醒引擎已启动")

    async def stop(self):
        """停止提醒引擎"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("提醒引擎已停止")

    async def _run_loop(self):
        """主循环：定时检查到期提醒"""
        while self._running:
            try:
                await self._check_reminders()
                await self._check_due_todos()
            except Exception as e:
                logger.error(f"提醒检查出错: {e}")
            await asyncio.sleep(self._check_interval)

    async def _check_reminders(self):
        """检查到期的提醒"""
        conn = get_connection()
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

        rows = conn.execute(
            """SELECT r.id, r.text, r.todo_id, r.repeat, t.title as todo_title
               FROM reminders r
               LEFT JOIN todos t ON r.todo_id = t.id
               WHERE r.triggered = 0 AND r.remind_at_utc <= ?""",
            (now,),
        ).fetchall()

        if not rows:
            return

        for row in rows:
            r = dict(row)
            logger.info(f"触发提醒 #{r['id']}: {r['text']}")

            # 标记已触发
            conn.execute("UPDATE reminders SET triggered = 1 WHERE id = ?", (r["id"],))

            # 如果是重复提醒，创建下一次
            if r["repeat"]:
                # 简化处理：每天重复就加一天
                from datetime import timedelta
                next_time = datetime.fromisoformat(r["remind_at_utc"]) + timedelta(days=1)
                conn.execute(
                    """INSERT INTO reminders (todo_id, text, remind_at_utc, repeat)
                       VALUES (?, ?, ?, ?)""",
                    (r["todo_id"], r["text"], next_time.strftime("%Y-%m-%dT%H:%M:%S"), r["repeat"]),
                )

            conn.commit()

            # 推送
            if self._push_callback:
                await self._push_callback({
                    "type": "reminder",
                    "text": r["text"],
                    "todo_id": r["todo_id"],
                    "todo_title": r["todo_title"],
                })

    async def _check_due_todos(self):
        """检查到期待办（截止时间在 24 小时内且未提醒过的）"""
        conn = get_connection()
        from datetime import timedelta

        now = datetime.utcnow()
        soon = (now + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
        now_str = now.strftime("%Y-%m-%dT%H:%M:%S")

        rows = conn.execute(
            """SELECT id, title, deadline_utc, deadline_text, source
               FROM todos
               WHERE status = 'pending'
                 AND deadline_utc IS NOT NULL
                 AND deadline_utc <= ?
                 AND deadline_utc >= ?""",
            (soon, now_str),
        ).fetchall()

        for row in rows:
            t = dict(row)
            # 检查是否已经发过提醒
            existing = conn.execute(
                "SELECT id FROM reminders WHERE todo_id = ? AND text LIKE '%即将截止%'",
                (t["id"],),
            ).fetchone()

            if not existing:
                remind_text = f"⚠️ 即将截止：{t['title']}"
                if t["deadline_text"]:
                    remind_text += f"（{t['deadline_text']}）"
                else:
                    remind_text += f"（截止 {t['deadline_utc']}）"

                conn.execute(
                    "INSERT INTO reminders (todo_id, text, remind_at_utc) VALUES (?, ?, ?)",
                    (t["id"], remind_text, now_str),
                )
                conn.commit()

                # 更新待办状态
                conn.execute(
                    "UPDATE todos SET status = 'reminding', updated_at = datetime('now') WHERE id = ?",
                    (t["id"],),
                )
                conn.commit()

                if self._push_callback:
                    await self._push_callback({
                        "type": "due_soon",
                        "text": remind_text,
                        "todo_id": t["id"],
                        "deadline_utc": t["deadline_utc"],
                    })
