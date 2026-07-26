"""Javis 主入口
FastAPI 应用初始化与路由注册。
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from db.database import init_db, close_db
from api import chat, notification, todo, system
from api import reminders_api as reminder
from api import memories_api as memory
from api import habits
from api import news
from api import bridge
from api import course
from api import expenses
from agent.reminder import ReminderEngine
from agent.scheduler import TaskScheduler
from api.chat import ws_manager


# ============================================================
# 日志配置
# ============================================================

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# ============================================================
# 提醒引擎（全局单例）
# ============================================================

reminder_engine = ReminderEngine()


# ============================================================
# 应用生命周期
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭时自动运行"""
    logger.info("Javis 正在启动...")

    # 初始化数据库
    init_db()

    # 设置提醒引擎的回调（推送到 WebSocket）
    async def push_to_user(reminder_data: dict):
        await ws_manager.broadcast("default", reminder_data)

    reminder_engine.set_push_callback(push_to_user)

    # 启动提醒引擎
    await reminder_engine.start()

    # 启动定时调度器
    scheduler = TaskScheduler()
    import asyncio
    asyncio.create_task(scheduler.start())

    logger.info(f"Javis 已启动 → http://{settings.host}:{settings.port}")

    yield

    # 关闭
    await reminder_engine.stop()
    await scheduler.stop()
    close_db()
    logger.info("Javis 已关闭")


# ============================================================
# 应用创建
# ============================================================

app = FastAPI(
    title="Javis",
    description="个人 AI 助手 - 全端 + 自主决策 Agent",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS（允许网页版和 Flutter App 跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(notification.router)
app.include_router(todo.router)
app.include_router(system.router)
app.include_router(reminder.router)
app.include_router(memory.router)
app.include_router(habits.router)
app.include_router(news.router)
app.include_router(bridge.router)
app.include_router(course.router)
app.include_router(expenses.router)

# 挂载静态文件（网页版）
app.mount("/", StaticFiles(directory="web", html=True), name="web")


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
