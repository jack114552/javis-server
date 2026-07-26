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
    new_id = cur.lastrowid
    logger.info(f"已设置待办+提醒 #{new_id}: {text} @ {remind_at_utc}")
    return {"success": True, "id": new_id, "text": text}


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


# ============================================================
# #6 记忆可修改 — delete_memory / update_memory
# ============================================================

def delete_memory(memory_id: int) -> Dict[str, Any]:
    """删除一条记忆"""
    conn = get_connection()
    cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()
    if cur.rowcount == 0:
        return {"success": False, "error": f"记忆 #{memory_id} 不存在"}
    logger.info(f"已删除记忆 #{memory_id}")
    return {"success": True, "id": memory_id}


def update_memory(memory_id: int, content: str, category: Optional[str] = None, tags: Optional[str] = None) -> Dict[str, Any]:
    """更新一条记忆的内容

    Args:
        memory_id: 记忆ID
        content: 新的内容
        category: 新的分类（可选）
        tags: 新的标签（可选）
    """
    conn = get_connection()
    existing = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if not existing:
        return {"success": False, "error": f"记忆 #{memory_id} 不存在"}

    new_category = category if category is not None else existing["category"]
    new_tags = tags if tags is not None else existing["tags"]

    conn.execute(
        "UPDATE memories SET content = ?, category = ?, tags = ? WHERE id = ?",
        (content, new_category, new_tags, memory_id),
    )
    conn.commit()
    logger.info(f"已更新记忆 #{memory_id}")
    return {"success": True, "id": memory_id}


# ============================================================
# #19 灵感快记 — add_quick_note
# ============================================================

def add_quick_note(content: str, tags: str = "") -> Dict[str, Any]:
    """快速记灵感 — 往 memory 表里存一条带 quick_note 标签的记录

    Args:
        content: 灵感内容
        tags: 额外标签，逗号分隔（可选）
    """
    conn = get_connection()
    full_tags = "quick_note"
    if tags:
        full_tags += "," + tags
    cur = conn.execute(
        "INSERT INTO memories (content, category, tags) VALUES (?, 'quick_note', ?)",
        (content, full_tags),
    )
    conn.commit()
    mid = cur.lastrowid
    logger.info(f"已保存灵感快记 #{mid}: {content[:50]}")
    return {"success": True, "id": mid, "content": content}


# ============================================================
# #21 记账本 — add_expense / query_expenses
# ============================================================

def add_expense(amount: float, category: str, description: str = "", date: Optional[str] = None) -> Dict[str, Any]:
    """记一笔账

    Args:
        amount: 金额
        category: 分类，如 餐饮、交通、购物、娱乐、其他
        description: 备注描述（可选）
        date: 日期 YYYY-MM-DD（可选，默认今天）
    """
    conn = get_connection()
    if not date:
        date = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    cur = conn.execute(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        (amount, category, description, date),
    )
    conn.commit()
    eid = cur.lastrowid
    logger.info(f"已记账 #{eid}: {category} {amount}元")
    return {"success": True, "id": eid, "amount": amount, "category": category}


def query_expenses(days: int = 7, category: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """查询近期账单

    Args:
        days: 查询最近多少天（默认7天）
        category: 按分类筛选（可选）
        limit: 最大返回条数
    """
    from datetime import timedelta
    conn = get_connection()
    cutoff = (datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=days)).strftime("%Y-%m-%d")

    if category:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date >= ? AND category = ? ORDER BY date DESC, created_at DESC LIMIT ?",
            (cutoff, category, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date >= ? ORDER BY date DESC, created_at DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()

    expenses = [dict(r) for r in rows]

    # 统计汇总
    total = sum(e["amount"] for e in expenses)
    by_category = {}
    for e in expenses:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]

    return {
        "success": True,
        "expenses": expenses,
        "count": len(expenses),
        "total": round(total, 2),
        "by_category": by_category,
    }


# ============================================================
# #16 日程规划 — plan_schedule
# ============================================================

def plan_schedule(tasks_json: str, date: str) -> Dict[str, Any]:
    """规划某天的日程安排 — 解析任务列表，按优先级/截止时间排序生成时间表

    Args:
        tasks_json: 任务列表 JSON，格式 [{"name": "任务名", "duration_min": 30, "priority": "high", "deadline": "18:00"}]
                    priority: high / medium / low，deadline 可选
        date: 日期 YYYY-MM-DD
    Returns:
        时间表
    """
    try:
        tasks = json.loads(tasks_json)
    except json.JSONDecodeError:
        return {"success": False, "error": "tasks_json 格式错误，需要合法 JSON 数组"}

    if not isinstance(tasks, list):
        return {"success": False, "error": "tasks_json 需要是数组"}

    # 优先级分值
    priority_scores = {"high": 3, "medium": 2, "low": 1}

    # 排序：有截止时间的先排，再按优先级
    def sort_key(t):
        has_deadline = 1 if t.get("deadline") else 0
        score = priority_scores.get(t.get("priority", "medium"), 2)
        return (-has_deadline, -score, t.get("deadline", ""))

    sorted_tasks = sorted(tasks, key=sort_key)

    # 生成时间表（从 09:00 开始，按 duration 递增）
    schedule = []
    current_hour = 9
    for t in sorted_tasks:
        name = t.get("name", "未命名任务")
        duration = t.get("duration_min", 60)
        priority = t.get("priority", "medium")
        deadline = t.get("deadline", "")

        start_h = current_hour
        start_m = 0
        end_h = start_h + duration // 60
        end_m = duration % 60
        time_slot = f"{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}"
        current_hour = end_h + 1  # 中间留 1 小时缓冲

        schedule.append({
            "name": name,
            "time": time_slot,
            "duration_min": duration,
            "priority": priority,
            "deadline": deadline,
        })

    # 存入记忆
    conn = get_connection()
    schedule_text = json.dumps(schedule, ensure_ascii=False)
    conn.execute(
        "INSERT INTO memories (content, category, tags) VALUES (?, 'schedule', ?)",
        (f"{date} 日程安排:\n" + "\n".join(
            f"  {s['time']} [{s['priority']}] {s['name']}" for s in schedule
        ), f"schedule,plan,{date}"),
    )
    conn.commit()

    return {
        "success": True,
        "date": date,
        "schedule": schedule,
        "total_tasks": len(schedule),
        "readable": "\n".join(f"{s['time']} [{s['priority']}] {s['name']}" for s in schedule),
    }


# ============================================================
# #12/#18 课程表 — query_schedule
# ============================================================

def query_schedule(day: str) -> Dict[str, Any]:
    """查询某天的课程安排

    Args:
        day: 星期几（1-7 或 中文 周一~周日）或日期 YYYY-MM-DD
    Returns:
        课程列表
    """
    conn = get_connection()

    # 解析 day 参数
    weekday_map = {"周一": 1, "周二": 2, "周三": 3, "周四": 4, "周五": 5, "周六": 6, "周日": 7,
                   "星期一": 1, "星期二": 2, "星期三": 3, "星期四": 4, "星期五": 5, "星期六": 6, "星期日": 7}
    day_of_week = None

    if day in weekday_map:
        day_of_week = weekday_map[day]
    elif day.isdigit() and 1 <= int(day) <= 7:
        day_of_week = int(day)
    else:
        # 尝试解析为日期
        try:
            dt = datetime.strptime(day, "%Y-%m-%d")
            day_of_week = dt.isoweekday()  # 1=周一
            # 计算当前是第几周
            week_num = dt.isocalendar()[1]
            week_parity = "odd" if week_num % 2 == 1 else "even"
        except ValueError:
            return {"success": False, "error": f"无法解析日期: {day}，请使用 1-7、周一~周日 或 YYYY-MM-DD 格式"}

    # 查询课程
    if day_of_week is not None:
        rows = conn.execute(
            """SELECT * FROM courses
               WHERE day_of_week = ?
               ORDER BY start_time ASC""",
            (day_of_week,),
        ).fetchall()
    else:
        rows = []

    courses = [dict(r) for r in rows]

    # 如果是具体日期，过滤周次
    if "week_parity" in dir():
        filtered = []
        for c in courses:
            if c["week_type"] == "all":
                filtered.append(c)
            elif c["week_type"] == week_parity:
                filtered.append(c)
        courses = filtered

    weekday_names = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}

    return {
        "success": True,
        "day": day,
        "day_of_week": day_of_week,
        "weekday_name": weekday_names.get(day_of_week, ""),
        "courses": courses,
        "count": len(courses),
    }


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

def send_notification(title: str, body: str = "") -> Dict[str, Any]:
    """主动向用户推送通知
    当你有重要信息需要告知用户时使用，比如提醒、新闻推送、日程建议等。
    通知会推送到手机通知栏和桌面。

    Args:
        title: 通知标题，简短概括内容
        body: 通知正文，详细说明
    Returns:
        推送结果
    """
    import json, urllib.request
    try:
        # 1. 通过 WebSocket 推送到手机
        from api.chat import ws_manager
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast("default", {
                    "type": "notification",
                    "title": title,
                    "body": body,
                }))
        except:
            pass

        # 2. 通过桥接推送到 BaiLongma（桌面通知）
        try:
            data = json.dumps({
                "content": f"[Javis 通知] {title}\n{body}",
                "channel": "API"
            }).encode()
            req = urllib.request.Request(
                "http://127.0.0.1:3722/message",
                data=data, headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except:
            pass

        logger.info(f"已推送通知: {title}")
        return {"success": True, "title": title}
    except Exception as e:
        return {"success": False, "error": str(e)}


def call_bailongma(content: str) -> Dict[str, Any]:
    """调用电脑上的白龙马 Agent 执行任务
    当用户说"跟白龙马说""让白龙马做""查个文件""搜一下电脑""打开什么""运行什么"时用这个工具。
    白龙马可以联网搜索、操作桌面文件、打开网页、执行 Shell 命令等。
    **注意：这是调用电脑端 Agent，不是创建待办！不要跟 add_todo 搞混。**

    Args:
        content: 发送给白龙马的任务描述，如 "搜索今天的科技新闻"
    Returns:
        操作结果
    """
    import urllib.request, json
    import time
    try:
        data = json.dumps({"content": content, "channel": "API"}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:3722/message",
            data=data, headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        
        conv_id = result.get("conversation_id")
        if not conv_id:
            return {"success": True, "result": result}
        
        # 记录当前消息数，等白龙马回复
        try:
            req_pre = urllib.request.Request(
                "http://127.0.0.1:3722/conversations",
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(req_pre, timeout=3) as resp_pre:
                msgs_before = json.loads(resp_pre.read())
            before_count = len(msgs_before)
        except:
            before_count = 0
        
        # 等待白龙马回复（最多等 25 秒），合并多段回复
        replies = []
        for _ in range(25):
            time.sleep(1)
            try:
                req2 = urllib.request.Request(
                    "http://127.0.0.1:3722/conversations",
                    headers={"Accept": "application/json"},
                )
                with urllib.request.urlopen(req2, timeout=5) as resp2:
                    msgs = json.loads(resp2.read())
                if len(msgs) > before_count:
                    for m in msgs[before_count:]:
                        role = (m.get("role") or "").lower()
                        if role in ("jarvis", "assistant") and m.get("content"):
                            replies.append(m["content"])
                    if replies:
                        return {"success": True, "reply": "\n\n".join(replies)}
            except:
                pass
        
        return {"success": True, "reply": "（白龙马处理中，但暂无回复）"}
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
    import urllib.request, urllib.parse, json, re

    api_key = settings.search_api_key
    results = []

    # 方案 1: Brave Search API（需翻墙）
    if api_key:
        try:
            req = urllib.request.Request(
                f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=5",
                headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
                for item in data.get("web", {}).get("results", []):
                    results.append({
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                    })
                return {"success": True, "results": results, "count": len(results)}
        except:
            pass

    # 方案 2: Bing（国内可访问）
    try:
        url = f"https://cn.bing.com/search?q={urllib.parse.quote(query)}&count=5"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # 解析 Bing 搜索结果
            for block in html.split('<li class="b_algo"')[1:]:
                try:
                    href_start = block.find('href="')
                    if href_start == -1: continue
                    href_start += 6
                    href_end = block.find('"', href_start)
                    link_url = block[href_start:href_end]
                    
                    a_end = block.find("</a>")
                    if a_end == -1: continue
                    title_section = block[block.find(">", block.find("<h2")) + 1:a_end] if "<h2" in block else ""
                    title = re.sub(r'<[^>]+>', '', title_section).strip()
                    
                    # 提取描述
                    desc = ""
                    p_start = block.find('<p')
                    if p_start != -1:
                        p_content_start = block.find('>', p_start) + 1
                        p_end = block.find('</p>', p_content_start)
                        if p_end != -1:
                            desc = re.sub(r'<[^>]+>', '', block[p_content_start:p_end]).strip()[:200]
                    
                    if title and link_url and "bing.com" not in link_url and "r.bing.com" not in link_url:
                        results.append({"title": title, "description": desc, "url": link_url})
                except:
                    pass
            if results:
                return {"success": True, "results": results[:5], "count": min(len(results), 5)}
    except:
        pass

    # 方案 3: DuckDuckGo 兜底
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.loads(resp.read())
            for topic in data.get("RelatedTopics", []):
                if "Text" in topic:
                    results.append({"title": topic["Text"][:100], "url": topic.get("FirstURL", "")})
            return {"success": True, "results": results[:5], "count": len(results[:5])}
    except Exception as e:
        return {"success": False, "error": f"搜索失败: {e}"}


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
tool_registry.register(delete_memory)
tool_registry.register(update_memory)
tool_registry.register(add_quick_note)
tool_registry.register(add_expense)
tool_registry.register(query_expenses)
tool_registry.register(plan_schedule)
tool_registry.register(query_schedule)
tool_registry.register(get_current_time)
tool_registry.register(get_weather)
tool_registry.register(web_search)
tool_registry.register(translate)
tool_registry.register(send_notification)
tool_registry.register(call_bailongma)
