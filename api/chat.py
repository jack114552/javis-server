"""对话 API（REST + WebSocket）
支持的交互方式：
1. REST POST /api/chat — 单轮对话
2. WebSocket /ws — 实时双向对话（推荐）
"""

import json
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from db.database import get_connection
from agent.engine import AgentEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])
engine = AgentEngine()


def _rebuild_history(rows: List) -> List[Dict[str, Any]]:
    """从数据库行还原完整对话历史，包括 tool 消息
    rows 是 sqlite3.Row 对象列表，支持字典式访问 [] 但不支持 .get()
    """
    history: List[Dict[str, Any]] = []
    for r in rows:
        role = r["role"]
        content = r["content"] or ""
        
        if role in ("user", "system"):
            history.append({"role": role, "content": content})
            
        elif role == "assistant":
            # 只还原 assistant 的自然语言回复
            # 不还原 tool_calls 和 tool 消息，因为：
            # 1. 存储的 tool_calls_log 不是 OpenAI 规范格式
            # 2. tool 消息必须有前导的 tool_calls，否则 DeepSeek 报错
            # 3. AI 的回复内容已包含工具执行结果（如"已设置提醒"）
            entry = {"role": "assistant", "content": content}
            history.append(entry)
                    
    return history


# ============================================================
# REST 接口
# ============================================================

class ChatMessage(BaseModel):
    session_id: str = "default"
    message: str


@router.post("/chat")
async def chat(message: ChatMessage):
    """发送一条消息给 AI，返回回复"""
    # 获取历史（正序）
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, tool_calls, tool_results FROM conversations WHERE session_id = ? ORDER BY created_at ASC LIMIT 30",
        (message.session_id,),
    ).fetchall()

    # 还原完整历史（含 tool 结果消息）
    history = _rebuild_history(rows)

    # 保存用户消息
    conn.execute(
        "INSERT INTO conversations (session_id, role, content) VALUES (?, 'user', ?)",
        (message.session_id, message.message),
    )
    conn.commit()

    # 调用 AI
    result = await engine.process_message(
        message=message.message,
        session_id=message.session_id,
        history=history,
    )

    # 保存 AI 回复
    conn.execute(
        "INSERT INTO conversations (session_id, role, content, tool_calls, tool_results) VALUES (?, 'assistant', ?, ?, ?)",
        (
            message.session_id,
            result.get("content", ""),
            json.dumps(result.get("tool_calls_log", []), ensure_ascii=False),
            json.dumps(result.get("tool_calls_log", []), ensure_ascii=False),
        ),
    )
    conn.commit()

    return result


# ============================================================
# WebSocket 接口
# ============================================================

class ConnectionManager:
    """WebSocket 连接管理"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str = "default"):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str = "default"):
        if session_id in self.active_connections:
            self.active_connections[session_id] = [
                ws for ws in self.active_connections[session_id] if ws != websocket
            ]

    async def broadcast(self, session_id: str, message: dict):
        """向指定 session 的所有连接广播消息"""
        if session_id not in self.active_connections:
            return
        for ws in self.active_connections[session_id]:
            try:
                await ws.send_json(message)
            except Exception:
                pass


# 全局连接管理器（供 reminder engine 推送使用）
ws_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
    """WebSocket 双向对话"""
    await ws_manager.connect(websocket, session_id)
    logger.info(f"WebSocket 连接建立: session={session_id}")

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                msg_data = json.loads(data)
                message = msg_data.get("message", data)
            except json.JSONDecodeError:
                message = data

            # 保存用户消息
            conn = get_connection()
            conn.execute(
                "INSERT INTO conversations (session_id, role, content) VALUES (?, 'user', ?)",
                (session_id, message),
            )
            conn.commit()

            # 获取历史（正序）
            rows = conn.execute(
                "SELECT role, content, tool_calls, tool_results FROM conversations WHERE session_id = ? ORDER BY created_at ASC LIMIT 30",
                (session_id,),
            ).fetchall()
            history = _rebuild_history(rows)

            # 流式调用 AI，逐 token 推送
            full_content = ""
            tool_results_log = []
            async for event in engine.process_message_stream(
                message=message, session_id=session_id, history=history,
            ):
                if event["type"] == "token":
                    full_content += event["content"]
                    await websocket.send_json({
                        "type": "token", "content": event["content"],
                    })
                elif event["type"] == "tool_start":
                    await websocket.send_json({
                        "type": "tool_start",
                        "name": event["name"],
                    })
                elif event["type"] == "tool_result":
                    tool_results_log.append({
                        "name": event["name"],
                    })
                elif event["type"] == "end":
                    full_content = event["data"].get("content", full_content)
                    break
                elif event["type"] == "error":
                    await websocket.send_json({
                        "type": "error", "content": event["content"],
                    })
                    return

            # 保存 AI 完整回复
            conn.execute(
                "INSERT INTO conversations (session_id, role, content, tool_calls, tool_results) VALUES (?, 'assistant', ?, ?, ?)",
                (
                    session_id,
                    full_content,
                    json.dumps(tool_results_log, ensure_ascii=False),
                    json.dumps(tool_results_log, ensure_ascii=False),
                ),
            )
            conn.commit()

            # 发送结束标记
            await websocket.send_json({
                "type": "chat_end",
                "content": full_content,
                "tool_calls": tool_results_log,
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        ws_manager.disconnect(websocket, session_id)
