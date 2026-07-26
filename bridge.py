"""白龙马桥接 API
让 Javis 与本地白龙马 Agent 互通。
"""
import logging, json
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bridge", tags=["bridge"])

# 白龙马本地地址（默认）
BAILONGMA_URL = "http://127.0.0.1:3721"


class BridgeMessage(BaseModel):
    content: str
    source: str = "javis"  # javis | bailongma
    session_id: str = "default"


@router.post("/send")
async def send_to_bailongma(msg: BridgeMessage):
    """转发消息到白龙马"""
    import urllib.request, urllib.error
    try:
        data = json.dumps({"message": msg.content}).encode()
        req = urllib.request.Request(
            f"{BAILONGMA_URL}/message",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        logger.info(f"已转发到白龙马: {msg.content[:50]}")
        return {"success": True, "bailongma_response": result}
    except urllib.error.URLError as e:
        logger.warning(f"白龙马连接失败: {e}")
        return {"success": False, "error": f"白龙马未运行: {e.reason}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/status")
async def check_bailongma():
    """检查白龙马是否在线"""
    import urllib.request, urllib.error
    try:
        with urllib.request.urlopen(f"{BAILONGMA_URL}/status", timeout=3) as resp:
            data = json.loads(resp.read())
        return {"online": True, "status": data}
    except Exception as e:
        return {"online": False, "error": str(e)}


@router.post("/notify")
async def receive_from_bailongma(msg: BridgeMessage):
    """接收白龙马发来的消息"""
    from agent.engine import AgentEngine
    engine = AgentEngine()
    result = await engine.process_message(
        message=f"[来自白龙马] {msg.content}",
        session_id=msg.session_id,
    )
    logger.info(f"处理白龙马消息完成: {msg.content[:50]}")
    return {"success": True, "response": result.get("content", "")}
