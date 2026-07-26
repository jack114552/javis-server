"""通知接收 API
手机端上报通知的入口，自动触发 AI 处理。
"""

import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


def _sanitize(text: str) -> str:
    """清洗通知文本，防止 prompt 注入"""
    # 去掉 html 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 限制长度
    text = text[:500]
    return text.strip()

from db.database import get_connection
from agent.engine import AgentEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
engine = AgentEngine()


class NotificationIn(BaseModel):
    """手机端上报的通知"""
    session_id: str = Field(default="default", description="用户会话 ID")
    app_name: str = Field(default="", description="来源应用名")
    title: str = Field(default="", description="通知标题")
    body: str = Field(default="", description="通知正文")
    received_at: Optional[str] = Field(default=None, description="手机端时间")


@router.post("")
async def receive_notification(notif: NotificationIn):
    """接收一条手机通知，自动提交给 AI 处理"""
    conn = get_connection()

    # 记录到日志
    received_at = notif.received_at or datetime.now().isoformat()
    cur = conn.execute(
        """INSERT INTO notification_log (session_id, app_name, title, body, received_at, processed)
           VALUES (?, ?, ?, ?, ?, 0)""",
        (notif.session_id, notif.app_name, notif.title, notif.body, received_at),
    )
    log_id = cur.lastrowid
    conn.commit()

    logger.info(f"收到通知 #{log_id}: [{notif.app_name}] {notif.title}")

    # 清洗通知内容，防止 prompt 注入
    safe_title = _sanitize(notif.title)
    safe_body = _sanitize(notif.body)
    safe_app = _sanitize(notif.app_name)

    # 调用 AI 处理通知
    message = f"收到来自【{safe_app}】的通知：\n标题：{safe_title}\n内容：{safe_body}"
    result = await engine.process_message(message, session_id=notif.session_id)

    # 标记已处理
    conn.execute("UPDATE notification_log SET processed = 1 WHERE id = ?", (log_id,))
    conn.commit()

    return {
        "success": True,
        "notification_id": log_id,
        "ai_response": result,
    }


@router.get("/history")
async def get_notification_history(limit: int = 50):
    """获取最近的通知历史"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notification_log ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return {"notifications": [dict(r) for r in rows]}
