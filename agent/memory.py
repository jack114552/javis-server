"""记忆系统
长期记忆的存储与检索。当前用 SQLite LIKE 匹配做基础检索，
后续可以接入向量数据库（如 chromadb）实现语义搜索。
"""

import logging
from typing import Any, Dict, List, Optional

from db.database import get_connection
from db.models import Memory

logger = logging.getLogger(__name__)


class MemoryManager:
    """长期记忆管理器"""

    @staticmethod
    def save(content: str, category: str = "general", tags: str = "") -> int:
        """保存一条记忆"""
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO memories (content, category, tags) VALUES (?, ?, ?)",
            (content, category, tags),
        )
        conn.commit()
        mid = cur.lastrowid
        logger.debug(f"记忆已保存: #{mid}")
        return mid

    @staticmethod
    def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索记忆（基础关键词匹配）"""
        conn = get_connection()
        rows = conn.execute(
            """SELECT id, content, category, tags, created_at
               FROM memories
               WHERE content LIKE ? OR tags LIKE ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_recent(limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近记忆"""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
