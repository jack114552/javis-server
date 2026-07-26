"""数据库连接与初始化
SQLite + WAL 模式，支持异步读写。
单人使用，不依赖外部数据库守护进程。
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

# 数据库连接（模块级单例）
_conn: Optional[sqlite3.Connection] = None


def get_connection() -> sqlite3.Connection:
    """获取数据库连接，首次调用时自动初始化"""
    global _conn
    if _conn is None:
        db_path = Path(settings.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL;")       # WAL 模式，支持读写并发
        _conn.execute("PRAGMA foreign_keys=ON;")         # 外键约束
        _conn.execute("PRAGMA busy_timeout=5000;")       # 忙等待 5s 后超时
        logger.info(f"数据库已连接: {db_path}")
    return _conn


def init_db():
    """初始化所有表结构，幂等执行"""
    conn = get_connection()
    cursor = conn.cursor()

    # 待办事项
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            description     TEXT DEFAULT '',
            deadline_utc    TEXT,               -- ISO 8601
            deadline_text   TEXT DEFAULT '',     -- 原文本
            source          TEXT DEFAULT '',     -- 来源 App
            priority        TEXT DEFAULT 'medium' CHECK(priority IN ('low','medium','high')),
            status          TEXT DEFAULT 'pending' CHECK(status IN ('pending','reminding','done','expired','cancelled')),
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    # 提醒（可独立于待办，也可以关联待办）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            todo_id         INTEGER REFERENCES todos(id) ON DELETE CASCADE,
            text            TEXT NOT NULL,
            remind_at_utc   TEXT NOT NULL,       -- ISO 8601
            triggered       INTEGER DEFAULT 0,   -- 0=等待, 1=已触发
            repeat          TEXT,                -- NULL / 'daily' / 'weekdays'
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    # 长期记忆
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            content         TEXT NOT NULL,
            category        TEXT DEFAULT 'general',
            tags            TEXT DEFAULT '',      -- 逗号分隔
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    # 对话历史
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            role            TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),
            content         TEXT,
            tool_calls      TEXT,                 -- JSON
            tool_results    TEXT,                 -- JSON
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_session
        ON conversations(session_id, created_at);
    """)

    # 通知日志（手机端上报的原始通知）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_cache (
            date            TEXT PRIMARY KEY,
            data            TEXT NOT NULL,
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            event_type      TEXT NOT NULL,
            value           TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            app_name        TEXT DEFAULT '',
            title           TEXT DEFAULT '',
            body            TEXT DEFAULT '',
            received_at     TEXT,                 -- 手机端的时间
            processed       INTEGER DEFAULT 0,    -- 0=未处理, 1=已处理
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    # Schema 版本管理
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INTEGER PRIMARY KEY,
            applied_at  TEXT DEFAULT (datetime('now'))
        );
    """)
    cursor.execute("""
        INSERT OR IGNORE INTO schema_version (version) VALUES (1);
    """)

    conn.commit()

      # 课程表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            teacher         TEXT DEFAULT '',
            location        TEXT DEFAULT '',
            day_of_week     INTEGER NOT NULL CHECK(day_of_week BETWEEN 1 AND 7),
            start_time      TEXT NOT NULL,
            end_time        TEXT NOT NULL,
            week_type       TEXT DEFAULT 'all' CHECK(week_type IN ('all','odd','even')),
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    # 记账本
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            amount          REAL NOT NULL,
            category        TEXT NOT NULL,
            description     TEXT DEFAULT '',
            date            TEXT NOT NULL,
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    # 执行增量迁移
    _run_migrations(conn)

    logger.info("数据库表结构初始化完成")


def _run_migrations(conn):
    """执行数据库增量迁移"""
    cursor = conn.cursor()
    current_version = cursor.execute(
        "SELECT MAX(version) FROM schema_version"
    ).fetchone()[0] or 0

    migrations = {
        # v2: 待办与提醒合并
        2: """
            ALTER TABLE todos ADD COLUMN remind_at_utc TEXT;
            ALTER TABLE todos ADD COLUMN repeat TEXT;
        """,
    }

    for version, sql in sorted(migrations.items()):
        if version > current_version:
            logger.info(f"执行数据库迁移 v{version}")
            try:
                for stmt in sql.strip().split(';'):
                    stmt = stmt.strip()
                    if stmt:
                        cursor.execute(stmt)
                cursor.execute(
                    "INSERT INTO schema_version (version) VALUES (?)", (version,)
                )
                conn.commit()
                logger.info(f"数据库迁移 v{version} 完成")
            except Exception as e:
                logger.warning(f"迁移 v{version} 失败（可能已存在）: {e}")
                conn.rollback()


def close_db():
    """关闭数据库连接"""
    global _conn
    if _conn:
        _conn.close()
        _conn = None
        logger.info("数据库连接已关闭")
