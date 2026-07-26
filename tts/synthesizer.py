"""TTS 语音合成模块
支持多种后端，当前为 Edge-TTS 实现（免费、中文质量好）。
对外提供统一接口：synthesize(text) -> bytes (MP3)。
"""

import io
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class TTSProvider(str, Enum):
    EDGE = "edge"
    NONE = "none"


class TTSConfig:
    """TTS 配置"""
    provider: TTSProvider = TTSProvider.EDGE
    voice: str = "zh-CN-XiaoxiaoNeural"  # Edge-TTS 中文女声
    speed: float = 1.0


class TTSEngine:
    """TTS 引擎"""

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()
        self._initialized = False

    async def initialize(self):
        """初始化 TTS 后端"""
        if self._initialized:
            return

        if self.config.provider == TTSProvider.EDGE:
            try:
                # 动态导入，避免依赖缺失导致启动失败
                import edge_tts
                self._client = edge_tts
                self._initialized = True
                logger.info("TTS 引擎已初始化: Edge-TTS")
            except ImportError:
                logger.warning("edge_tts 未安装，TTS 将使用 stub 模式")
                self.config.provider = TTSProvider.NONE
                self._initialized = True
        else:
            self._initialized = True

    async def synthesize(self, text: str) -> Optional[bytes]:
        """合成语音，返回 MP3 字节流

        Args:
            text: 要朗读的文本

        Returns:
            MP3 字节数据，失败返回 None
        """
        if not text:
            return None

        if self.config.provider == TTSProvider.EDGE and self._initialized:
            try:
                communicate = self._client.Communicate(text, self.config.voice)
                audio_data = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data.write(chunk["data"])
                audio_data.seek(0)
                return audio_data.read()
            except Exception as e:
                logger.error(f"TTS 合成失败: {e}")
                return None

        return None
