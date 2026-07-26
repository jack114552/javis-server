"""工具定义与注册
每个工具是一个函数，带有名称、描述、参数 schema。
AI 通过 Function Calling 自主决策调用哪些工具。
"""

import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

from db.database import get_connection
from db.models import Todo, Reminder, Memory

logger = logging.getLogger(__name__)


# ============================================================
# 工具函数实现
# ============================================================

def _now_iso(tz_str: str = "Asia/Shanghai") -> str:
    """返回当前时间的 ISO 8601 字符串（指定时区）"""
    return datetime.now(ZoneInfo(tz_str)).isoformat()


def add_todo(
    title: str,
    deadline_utc: Optional[str] = None,
    deadline_text: Optional[str] = None,
    source: str = "手动",
    priority: str = "medium",
    description: str = "",
) -> Dict[str, Any]:
    """添加一条待办事项"""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO todos (title, description, deadline_utc, deadline_text, source, priority, status)
           VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
        (title, description, deadline_utc, deadline_text or "", source, priority),
    )
    conn.commit()
    todo_id = cur.lastrowid
    logger.info(f"已添加待办 #{todo_id}: {title}")
    return {"success": True, "id": todo_id, "title": title}


def query_todos(
    status: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """查询待办事项列表"""
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

    todos = [dict(r) for r in rows]
    return {"success": True, "todos": todos, "count": len(todos)}


def complete_todo(todo_id: int) -> Dict[str, Any]:
    """标记待办为已完成"""
    conn = get_connection()
    cur = conn.execute(
        "UPDATE todos SET status = 'done', updated_at = datetime('now') WHERE id = ?",
        (todo_id,),
    )
    conn.commit()
    if cur.rowcount == 0:
        return {"success": False, "error": f"待办 #{todo_id} 不存在"}
    logger.info(f"已完成待办 #{todo_id}")
    return {"success": True, "id": todo_id}


def delete_todo(todo_id: int) -> Dict[str, Any]:
    """删除待办事项"""
    conn = get_connection()
    cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    if cur.rowcount == 0:
        return {"success": False, "error": f"待办 #{todo_id} 不存在"}
    logger.info(f"已删除待办 #{todo_id}")
    return {"success": True, "id": todo_id}


def set_reminder(
    text: str,
    remind_at_utc: str,
    todo_id: Optional[int] = None,
    repeat: Optional[str] = None,
) -> Dict[str, Any]:
    """设置一个提醒（创建带 remind_at 的待办）"""
    conn = get_connection()

    # 创建待办并设置提醒时间
    cur = conn.execute(
        """INSERT INTO todos (title, description, deadline_utc, deadline_text, source, priority, status, remind_at_utc, repeat)
           VALUES (?, '', ?, ?, '提醒', 'medium', 'pending', ?, ?)""",
        (text, remind_at_utc, text, remind_at_utc, repeat),
    )
    conn.commit()
    todo_id = cur.lastrowid
    logger.info(f"已设置待办+提醒 #{todo_id}: {text} @ {remind_at_utc}")
    return {"success": True, "id": rid, "text": text}


def delete_reminder(reminder_id: int) -> Dict[str, Any]:
    """删除一个提醒"""
    conn = get_connection()
    cur = conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    if cur.rowcount == 0:
        return {"success": False, "error": f"提醒 #{reminder_id} 不存在"}
    return {"success": True, "id": reminder_id}


def query_reminders(limit: int = 20) -> Dict[str, Any]:
    """查询所有提醒"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE triggered = 0 ORDER BY remind_at_utc ASC LIMIT ?",
        (limit,),
    ).fetchall()
    reminders = [dict(r) for r in rows]
    return {"success": True, "reminders": reminders, "count": len(reminders)}


def search_memory(query: str, limit: int = 10) -> Dict[str, Any]:
    """搜索长期记忆（关键词匹配 + 全文搜索）"""
    conn = get_connection()
    # SQLite FTS5 需要额外配置，先用 LIKE 模糊搜索
    rows = conn.execute(
        """SELECT id, content, category, tags, created_at
           FROM memories
           WHERE content LIKE ? OR tags LIKE ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (f"%{query}%", f"%{query}%", limit),
    ).fetchall()
    results = [dict(r) for r in rows]
    return {"success": True, "results": results, "count": len(results)}


def save_memory(content: str, category: str = "general", tags: str = "") -> Dict[str, Any]:
    """保存一条长期记忆"""
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO memories (content, category, tags) VALUES (?, ?, ?)",
        (content, category, tags),
    )
    conn.commit()
    mid = cur.lastrowid
    logger.info(f"已保存记忆 #{mid}: [{category}] {content[:50]}")
    return {"success": True, "id": mid}


def get_current_time(tz: str = "Asia/Shanghai") -> Dict[str, Any]:
    """获取当前时间，帮助 AI 理解时间上下文"""
    now = datetime.now(ZoneInfo(tz))
    return {
        "success": True,
        "time_iso": now.isoformat(),
        "timezone": tz,
        "weekday": now.weekday(),
        "readable": now.strftime("%Y年%m月%d日 %H:%M %A"),
    }


# ============================================================
# 新增工具
# ============================================================

def call_bailongma(action: str, params: str = "{}") -> Dict[str, Any]:
    """调用桌面白龙马 Agent 执行操作
    白龙马可以操作桌面文件、打开网页、执行 Shell 命令等

    Args:
        action: 操作类型，如 search_web / run_code / open_file / read_web
        params: JSON 参数，如 {"query": "今天天气"}
    Returns:
        操作结果
    """
    import urllib.request, json
    try:
        data = json.dumps({"action": action, "params": json.loads(params)}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:3721/message",
            data=data, headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": f"白龙马调用失败: {e}"}


def get_weather(location: str) -> Dict[str, Any]:
    """查询某个城市的天气

    Args:
        location: 城市名，如 北京、上海、杭州
    Returns:
        {"temperature", "condition", "humidity", "wind"}
    """
    import urllib.request
    import urllib.parse
    try:
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=j1"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            current = data["current_condition"][0]
            return {
                "success": True,
                "location": location,
                "temperature": current["temp_C"] + "°C",
                "condition": current["weatherDesc"][0]["value"],
                "humidity": current["humidity"] + "%",
                "wind": current["windspeedKmph"] + "km/h",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def web_search(query: str) -> Dict[str, Any]:
    """在互联网上搜索信息

    Args:
        query: 搜索关键词
    Returns:
        搜索结果列表
    """
    from config import settings
    import urllib.request
    import json
    
    api_key = settings.search_api_key
    
    try:
        if api_key:
            # 使用 Brave Search API
            req = urllib.request.Request(
                f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=5",
                headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                results = []
                for item in data.get("web", {}).get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                    })
                return {"success": True, "results": results, "count": len(results)}
        else:
            # 兜底：DuckDuckGo 免费接口
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
                results = []
                for topic in data.get("RelatedTopics", []):
                    if "Text" in topic:
                        results.append({"title": topic["Text"][:100], "url": topic.get("FirstURL", "")})
                return {"success": True, "results": results[:5], "count": len(results[:5])}
    except Exception as e:
        return {"success": False, "error": str(e)}


def translate(text: str, target_lang: str = "zh") -> Dict[str, Any]:
    """翻译文本到目标语言

    Args:
        text: 要翻译的文本
        target_lang: 目标语言代码，zh=中文，en=英文，ja=日文
    Returns:
        翻译结果
    """
    try:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode({
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang,
            "dt": "t",
            "q": text,
        }).encode()
        url = f"https://translate.googleapis.com/translate_a/single?{data.decode()}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            result = json.loads(resp.read())
            translated = result[0][0][0] if result and result[0] and result[0][0] else ""
            return {"success": True, "translated": translated, "target_lang": target_lang}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 工具注册表
# ============================================================

class ToolRegistry:
    """工具注册表，管理所有可用工具的定义与执行"""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, func: Callable) -> None:
        """注册一个工具函数，自动提取函数信息生成 schema"""
        import inspect

        sig = inspect.signature(func)
        params = sig.parameters

        # 构建 OpenAI Function Calling 格式的 parameters schema
        properties = {}
        required = []
        for name, param in params.items():
            # 推断类型
            if param.annotation is inspect.Parameter.empty:
                ptype = "string"
            elif param.annotation is int:
                ptype = "integer"
            elif param.annotation is float:
                ptype = "number"
            elif param.annotation is bool:
                ptype = "boolean"
            else:
                ptype = "string"

            prop = {"type": ptype}
            # 从 docstring 中提取参数描述（简化处理）
            if func.__doc__:
                # 查找参数描述行
                for line in func.__doc__.split("\n"):
                    line = line.strip()
                    if line.startswith(f":param {name}:"):
                        prop["description"] = line.split(":", 2)[-1].strip()

            properties[name] = prop

            # 判断是否必需
            if param.default is inspect.Parameter.empty:
                required.append(name)

        # 构建工具定义
        tool_def = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or "",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

        self._tools[func.__name__] = {
            "function": func,
            "openai_tool": tool_def,
        }

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """获取 OpenAI 格式的工具定义列表"""
        return [t["openai_tool"] for t in self._tools.values()]

    async def execute(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行工具函数（内部分配到线程池执行同步函数）"""
        if name not in self._tools:
            return {"success": False, "error": f"未知工具: {name}"}

        import asyncio
        func = self._tools[name]["function"]
        try:
            # 在默认事件循环的线程池中运行同步函数
            return await asyncio.to_thread(func, **args)
        except Exception as e:
            logger.error(f"工具 {name} 执行失败: {e}")
            return {"success": False, "error": str(e)}


# 全局工具注册表
tool_registry = ToolRegistry()

# 注册所有工具
tool_registry.register(add_todo)
tool_registry.register(query_todos)
tool_registry.register(complete_todo)
tool_registry.register(delete_todo)
tool_registry.register(set_reminder)
tool_registry.register(delete_reminder)
tool_registry.register(query_reminders)
tool_registry.register(search_memory)
tool_registry.register(save_memory)
tool_registry.register(get_current_time)
tool_registry.register(get_weather)
tool_registry.register(web_search)
tool_registry.register(translate)
tool_registry.register(call_bailongma)
