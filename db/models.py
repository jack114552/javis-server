"""数据模型定义
SQLite Row 的 Python 封装，提供类型安全的访问。
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Todo:
    """待办事项"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    deadline_utc: Optional[str] = None       # ISO 8601
    deadline_text: str = ""                  # 原始文本
    source: str = ""                         # 来源 App
    priority: str = "medium"                 # low / medium / high
    status: str = "pending"                  # pending / reminding / done / expired
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Reminder:
    """提醒"""
    id: Optional[int] = None
    todo_id: Optional[int] = None
    text: str = ""
    remind_at_utc: str = ""                  # ISO 8601
    triggered: int = 0
    repeat: Optional[str] = None             # None / daily / weekdays
    created_at: Optional[str] = None


@dataclass
class Memory:
    """长期记忆条目"""
    id: Optional[int] = None
    content: str = ""
    category: str = "general"
    tags: str = ""
    created_at: Optional[str] = None


@dataclass
class Course:
    """课程表"""
    id: Optional[int] = None
    name: str = ""
    teacher: str = ""
    location: str = ""
    day_of_week: int = 1          # 1=周一 至 7=周日
    start_time: str = ""           # HH:MM
    end_time: str = ""             # HH:MM
    week_type: str = "all"         # all / odd / even
    created_at: Optional[str] = None


@dataclass
class Expense:
    """记账条目"""
    id: Optional[int] = None
    amount: float = 0.0
    category: str = ""
    description: str = ""
    date: str = ""                  # YYYY-MM-DD
    created_at: Optional[str] = None


@dataclass
class Notification:
    """手机端上报的通知"""
    id: Optional[int] = None
    session_id: str = ""
    app_name: str = ""
    title: str = ""
    body: str = ""
    received_at: Optional[str] = None
    processed: int = 0
    created_at: Optional[str] = None
