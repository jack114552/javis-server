"""提醒列表 API（从 todos 表读取 remind_at 字段）"""
import logging
from fastapi import APIRouter, Query
from db.database import get_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("")
async def list_reminders(
    limit: int = Query(30, description="返回条数"),
):
    """获取即将提醒的待办（remind_at_utc 不为空 + 未完成的）"""
    conn = get_connection()
    rows = conn.execute(
        """SELECT id as todo_id, id, title as text, remind_at_utc, repeat,
                  deadline_text, priority, status, created_at
           FROM todos 
           WHERE remind_at_utc IS NOT NULL 
             AND status IN ('pending', 'reminding')
           ORDER BY remind_at_utc ASC LIMIT ?""",
        (limit,),
    ).fetchall()

    reminders = []
    for r in rows:
        d = dict(r)
        d['todo_title'] = d['text']
        reminders.append(d)

    return {"reminders": reminders, "count": len(reminders)}
