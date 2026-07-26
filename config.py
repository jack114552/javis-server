"""Javis 配置管理
从环境变量或 .env 文件读取配置，提供统一访问接口。
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置，优先读取环境变量，未设置则从 .env 文件读取"""

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8080

    # 数据库
    db_path: str = "data/javis.db"

    # LLM API（OpenAI 兼容格式）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # 用户
    timezone: str = "Asia/Shanghai"

    # Agent
    max_tool_rounds: int = 5
    notification_poll_interval: int = 15  # 分钟

    # 搜索 API
    search_api_key: str = ""

    # 日志
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局单例
settings = Settings()

# 确保数据库目录存在
_db_dir = Path(settings.db_path).parent
if _db_dir.name:
    _db_dir.mkdir(parents=True, exist_ok=True)
