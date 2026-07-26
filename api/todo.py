"""待办 CRUD API
直接操作待办事项，绕过 AI 的快速接口。
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/todos", tags=["todos"])


class TodoCreate(BaseModel):
    title: str
    description: str = ""
    deadline_utc: Optional[str] = None
    deadline_text: str = ""
    source: str = "手动"
    priority: str = "medium"


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline_utc: Optional[str] = None
    deadline_text: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    remind_at_utc: Optional[str] = None


@router.get("")
async def list_todos(
    status: Optional[str] = Query(None, description="过滤状态"),
    limit: int = Query(50, description="返回条数"),
):
    """获取待办列表"""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM todos WHERE status = ? ORDER BY deadline_utc ASC, created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM todos ORDER BY deadline_utc ASC, created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    return {"todos": [dict(r) for r in rows], "count": len(rows)}


@router.post("")
async def create_todo(todo: TodoCreate):
    """创建待办"""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO todos (title, description, deadline_utc, deadline_text, source, priority, status)
           VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
        (todo.title, todo.description, todo.deadline_utc, todo.deadline_text, todo.source, todo.priority),
    )
    conn.commit()
    todo_id = cur.lastrowid
    logger.info(f"手动创建待办 #{todo_id}: {todo.title}")
    return {"success": True, "id": todo_id}


@router.get("/{todo_id}")
async def get_todo(todo_id: int):
    """获取单个待办"""
    conn = get_connection()
    row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="待办不存在")
    return dict(row)


@router.patch("/{todo_id}")
async def update_todo(todo_id: int, update: TodoUpdate):
    """更新待办"""
    conn = get_connection()
    fields = []
    values = []
    for key, value in update.dict(exclude_unset=True).items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)
    if not fields:
        return {"success": False, "error": "没有需要更新的字段"}

    values.append(todo_id)
    fields.append("updated_at = datetime('now')")
    conn.execute(
        f"UPDATE todos SET {', '.join(fields)} WHERE id = ?",
        values,
    )
    conn.commit()
    return {"success": True}


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int):
    """删除待办"""
    conn = get_connection()
    cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="待办不存在")
    return {"success": True}
