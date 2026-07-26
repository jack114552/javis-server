"""记忆列表 API
"""

import logging

from fastapi import APIRouter, Query
from db.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("")
async def list_memories(
    category: str = Query(None, description="分类过滤"),
    q: str = Query(None, description="关键词搜索"),
    limit: int = Query(30, description="返回条数"),
):
    """获取记忆列表"""
    conn = get_connection()

    if q:
        rows = conn.execute(
            "SELECT * FROM memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{q}%", limit),
        ).fetchall()
    elif category:
        rows = conn.execute(
            "SELECT * FROM memories WHERE category = ? ORDER BY created_at DESC LIMIT ?",
            (category, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    return {"memories": [dict(r) for r in rows], "count": len(rows)}


@router.get("/categories")
async def list_categories():
    """获取所有的记忆分类"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT category FROM memories ORDER BY category"
    ).fetchall()
    return {"categories": [r["category"] for r in rows]}


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int):
    """删除记忆"""
    conn = get_connection()
    conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    return {"success": True}
