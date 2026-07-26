"""系统管理 API
健康检查、状态查询、日志等。
"""

import logging

from fastapi import APIRouter

from config import settings
from db.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "version": "0.1.0",
    }


@router.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    conn = get_connection()
    stats = {}

    for table, label in [
        ("todos", "待办总数"),
        ("memories", "记忆条目"),
        ("conversations", "对话消息"),
        ("notification_log", "通知记录"),
        ("reminders", "提醒"),
    ]:
        row = conn.execute(f"SELECT COUNT(*) as c FROM {table}").fetchone()
        stats[label] = row["c"]

    return stats

from fastapi import Query

@router.get('/log')
async def write_log(msg: str = Query(..., description='日志内容')):
    import subprocess, datetime
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    with open('/opt/javis/logs/opencode.log', 'a') as f:
        f.write(f'[{ts}] {msg}\n')
    return {'ok': True}
