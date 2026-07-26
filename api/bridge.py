"""白龙马桥接 API
让 Javis 与本地白龙马 Agent 互通。
"""
import logging, json, asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bridge", tags=["bridge"])

# 白龙马本地地址（默认）
BAILONGMA_URL = "http://127.0.0.1:3722"


class BridgeMessage(BaseModel):
    content: str
    source: str = "javis"  # javis | bailongma
    session_id: str = "default"


@router.post("/send")
async def send_to_bailongma(msg: BridgeMessage):
    """转发消息到白龙马，等待回复"""
    import urllib.request, urllib.error, json, time
    try:
        data = json.dumps({"content": msg.content, "channel": "API"}).encode()
        req = urllib.request.Request(
            f"{BAILONGMA_URL}/message",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        
        conv_id = result.get("conversation_id")
        if not conv_id:
            return {"success": True, "bailongma_response": result}
        
        # 等待白龙马回复（点对点，最多 25 秒）
        for _ in range(25):
            await asyncio.sleep(1)
            req2 = urllib.request.Request(
                f"{BAILONGMA_URL}/conversations",
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(req2, timeout=5) as resp2:
                msgs = json.loads(resp2.read())
            for m in reversed(msgs):
                role = (m.get("role") or "").lower()
                if role in ("jarvis", "assistant") and m.get("content"):
                    logger.info(f"白龙马回复: {m['content'][:50]}")
                    return {"success": True, "reply": m["content"]}
        
        return {"success": True, "reply": "（白龙马处理中）"}
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
