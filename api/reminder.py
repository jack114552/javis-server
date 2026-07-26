"""提醒列表 API
"""

import logging

from fastapi import APIRouter, Query
from db.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("")
async def list_reminders(
    triggered: int = Query(0, description="0=未触发 1=已触发"),
    limit: int = Query(30, description="返回条数"),
):
    """获取提醒列表"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.*, t.title as todo_title, t.deadline_text 
           FROM reminders r 
           LEFT JOIN todos t ON r.todo_id = t.id 
           WHERE r.triggered = ? 
           ORDER BY r.remind_at_utc ASC LIMIT ?""",
        (triggered, limit),
    ).fetchall()

    return {"reminders": [dict(r) for r in rows], "count": len(rows)}
