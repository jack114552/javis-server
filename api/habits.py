"""习惯数据采集 API
接收手机端上报的使用习惯数据（屏幕状态、WiFi、App 使用等）
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/habits", tags=["habits"])


class HabitEvent(BaseModel):
    event_type: str  # screen_on | screen_off | wifi_connected | wifi_disconnected
    value: str = ""  # wifi SSID 等
    session_id: str = "default"


@router.post("")
async def record_habit(event: HabitEvent):
    """记录一条习惯事件"""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO habit_events (session_id, event_type, value) VALUES (?, ?, ?)",
        (event.session_id, event.event_type, event.value),
    )
    conn.commit()
    return {"success": True, "id": cur.lastrowid}
