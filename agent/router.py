"""
意图路由器
在消息到达 AI 引擎前做快速分类，决定使用哪个提示词模式和工具白名单。
"""
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ============================================================
# 模式定义
# ============================================================

MODES = {
    "chat": {
        "name": "通用对话",
        "description": "默认模式，闲聊、问答、日常交流",
    },
    "bailongma": {
        "name": "白龙马桥接",
        "description": "消息直接转发给白龙马，AI 不做任何处理",
    },
    "todo": {
        "name": "待办操作",
        "description": "创建、查询、管理待办事项",
    },
    "search": {
        "name": "搜索查询",
        "description": "联网搜索、查询信息",
    },
    "memory": {
        "name": "记忆操作",
        "description": "保存、查询、修改记忆",
    },
}

# ============================================================
# 模式切换关键词
# ============================================================

# 进入 BaiLongma 模式
BAILONGMA_ENTER = [
    r"跟白龙马说",
    r"让白龙马",
    r"传给白龙马",
    r"叫白龙马",
    r"问白龙马",
    r"白龙马[，,]\s*",
    r"^对白龙马说",
    r"^告诉白龙马",
    r"转发给白龙马",
    r"查(个|一下|一|下)文件",
    r"搜(索|一下|一)电脑",
    r'打开.*(白龙马|桌面|电脑)',    r"帮我看看(电脑|桌面|文件)",
]

# 退出 BaiLongma 模式
BAILONGMA_EXIT = [
    r"^好(了|吧)",
    r"^行了",
    r"^够了",
    r"^回来",
    r"^结束",
    r"^退出(白龙马)",
    r"^不(用了|问了|查了)",
    r"^回到(对话|聊天)",
    r"^继续说",
]

# 待办模式关键词
TODO_KEYWORDS = [
    r"记(一下|住|录)",
    r"添加待办",
    r"提醒我",
    r"记得(做|要|去|买|拿|带)",
    r"新建待办",
    r"待办[了。，]",
    r"^别忘(了|记)",
]

# 搜索模式关键词
SEARCH_KEYWORDS = [
    r"搜索",
    r"查(一下|一|找|询)",
    r"搜(索|一下|一找)",
    r"找(一下|一找|找)",
    r"今天(的)?新闻",
    r"(什么|怎么|为什么|哪里|如何|多少)",
]

# ============================================================
# 会话状态
# ============================================================

class SessionState:
    """每个会话的当前模式状态"""

    def __init__(self):
        self.reset()

    def reset(self, mode: str = "chat"):
        self.mode = mode
        self.last_tool = None
        self.last_summary = ""
        self.bailongma_message_count = 0

    def to_prompt_fragment(self) -> str:
        """生成当前状态的提示词片段"""
        if self.mode == "bailongma":
            return (
                "\n## 当前状态\n"
                f"- 当前模式: 白龙马桥接（已连续发送 {self.bailongma_message_count} 条消息给白龙马）\n"
                "- 规则: 用户的每条消息都直接转发给白龙马，不要自己理解或处理\n"
                "- 退出方式: 用户说\"好了\"\"回来\"\"结束\"\"退出白龙马\"时回到普通对话\n"
                f"- 上一条消息摘要: {self.last_summary or '无'}\n"
            )
        return ""


# 全局会话状态存储
_sessions: Dict[str, SessionState] = {}


def get_session(session_id: str = "default") -> SessionState:
    """获取或创建会话状态"""
    if session_id not in _sessions:
        _sessions[session_id] = SessionState()
    return _sessions[session_id]


def classify_intent(message: str, session_id: str = "default") -> str:
    """对用户消息进行意图分类，返回模式名称"""
    state = get_session(session_id)

    # 1. 检查是否要退出当前模式
    if state.mode != "chat":
        for pattern in BAILONGMA_EXIT:
            if re.search(pattern, message):
                logger.info(f"意图路由: 退出 {state.mode} 模式 → chat")
                state.reset("chat")
                return "chat"

    # 2. BaiLongma 模式优先（一旦进入，所有消息自动转发）
    if state.mode == "bailongma":
        state.bailongma_message_count += 1
        state.last_summary = message[:30]
        return "bailongma"

    # 3. 检查是否要进入 BaiLongma 模式
    for pattern in BAILONGMA_ENTER:
        if re.search(pattern, message):
            logger.info(f"意图路由: chat → bailongma")
            state.mode = "bailongma"
            state.bailongma_message_count = 1
            state.last_summary = message[:30]
            return "bailongma"

    # 4. 待办模式
    for pattern in TODO_KEYWORDS:
        if re.search(pattern, message):
            logger.info(f"意图路由: todo")
            state.last_tool = "add_todo"
            return "todo"

    # 5. 搜索模式
    has_question = False
    for pattern in SEARCH_KEYWORDS:
        if re.search(pattern, message):
            has_question = True
            break
    if has_question:
        logger.info(f"意图路由: search")
        state.last_tool = "web_search"
        return "search"

    # 6. 默认聊天
    state.mode = "chat"
    return "chat"
