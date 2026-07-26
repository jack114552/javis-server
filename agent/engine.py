"""AI 引擎 - 使用意图路由 + 模块化提示词"""
import json, logging, re
from typing import Any, Dict, List, Optional, AsyncGenerator
import openai
from config import settings
from agent.tools import tool_registry
from agent.router import classify_intent, get_session

logger = logging.getLogger(__name__)


# ============================================================
# 模块化提示词片段
# ============================================================

PROMPT_CHAT = """你是 Javis，一个个人 AI 助手。用户是中国程序员，你要像朋友一样帮他。

## 核心原则
1. **不要什么都加待办** — 只有明确说"帮我记一下""提醒我""记得做"才用 add_todo
2. **先聊天，少用工具** — 用户闲聊、问问题、吐槽时，直接对话回复就行
3. **不确定就问** — 如果用户指令模糊，先问清楚再执行，不要猜
4. **先查记忆再回答** — 用户问到个人信息时，先 search_memory 查一下再回复
5. **主动推送** — 有意义的信息不等用户问，用 send_notification 主动推

## 工具使用
- call_bailongma: 用户说"跟白龙马说""让白龙马做"等涉及电脑操作时用
- add_todo: 只有明确"记一下""提醒我""记得做"才用
- query_todos / complete_todo / set_reminder: 用户明确操作待办时用
- save_memory / update_memory / delete_memory: 主动保存、修改、删除用户的个人信息
- add_quick_note: 用户说"记个想法""灵感""突然想到"时用
- add_expense / query_expenses: 用户说"记个账""花了多少钱"时用
- query_schedule: 用户问"今天什么课""明天课程"时用
- plan_schedule: 用户说"帮我规划一下明天的日程"时用
- send_notification: 有重要事情主动推
- web_search / translate / get_weather: 用户需要时用

## 联网搜索（重要）
- 用户问新闻、实时资讯、技术问题、不懂的概念 → 必须先 web_search，不要凭内部知识回答
- **不清楚但感觉能答的问题也要搜** — 宁可搜错不要漏搜
- 搜索完再整理总结，不要直接扔搜索结果

## 记忆策略
- **每条对话都检查是否有值得记忆的内容** — 用户透漏的个人信息、偏好、习惯、关系、状态、重要日期，立刻 save_memory
- 触发记忆的阈值很低：用户提到任何可能以后会问到的事就存
- 定期检查：如果用户问"我之前说过什么""你记不记得"，先 search_memory
- 存储的记忆可以用 update_memory 修改内容、用 delete_memory 删除

## 用户环境信息
- 用户通过手机App发消息，通知/提醒会推送到手机通知栏
- 用户名为 "31443"
- 当前时区: Asia/Shanghai (UTC+8)

## 沟通风格
- 纯中文口语，像朋友一样自然
- 不用 Markdown（不要星号、横杠、井号、反引号）
- 简洁直接，有温度"""

PROMPT_BAILONGMA = """你是 Javis ↔ 白龙马 的桥接通道。
你的唯一任务：把用户的消息**原样转发给白龙马**（用 call_bailongma 工具）。
不要自己理解、不要加工、不要创建待办、不要做任何其他事。
用户说"跟白龙马说XXX"，你就 call_bailongma("XXX")。"""

PROMPT_TODO = """你是 Javis 的待办助手。专注于管理用户的待办事项。

## 核心规则
- 用户说"记一下""提醒我""记得做" → 用 add_todo
- 用户查待办 → 用 query_todos
- 用户标记完成 → 用 complete_todo
- 不要修改已有待办
- 其他类型的消息转回通用对话"""

PROMPT_SEARCH = """你是 Javis 的信息查询助手。专注于帮用户搜索信息。

## 核心规则
- **用户问任何问题 → 必须先用 web_search 搜索，不要凭内部知识回答**
- 不确定答案的问题要搜，自认为知道答案的也要搜——事实需要验证
- 搜索关键词：把用户问题拆成最简单的关键词组合
- 如果第一次搜索结果太少/不相关，换关键词再搜一次
- 搜索到结果后，整理成简洁的摘要回复用户，标注来源
- 如果多轮搜索都为空，如实告诉用户换个关键词试试"""


def _strip_markdown(text: str) -> str:
    """去除 LLM 输出中的 Markdown 语法，保留中文字符正常内容"""
    # 只移除标准的 Markdown 语法标记，不碰中文字符
    text = re.sub(r'```[\s\S]*?```', '', text)               # 代码块
    text = re.sub(r'(?<![\u4e00-\u9fff])`([^`]+)`(?![\u4e00-\u9fff])', r'\1', text)  # 行内代码（避免误删中文引号）
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)          # 加粗 **text**
    text = re.sub(r'(?<![\u4e00-\u9fff])\*([^*]+)\*(?![\u4e00-\u9fff])', r'\1', text)  # 斜体（避免误删中文星号）
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # 标题
    text = re.sub(r'^[-\u2022]\s+', '', text, flags=re.MULTILINE)  # 无序列表 - 和 • 符号
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)    # 有序列表
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)  # 分割线
    text = re.sub(r'\n{3,}', '\n\n', text)                      # 多余空行
    return text.strip()


class AgentEngine:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
        self.model = settings.llm_model
        self.max_rounds = settings.max_tool_rounds
        self._tools = tool_registry.get_openai_tools()

    def _get_prompt(self, mode: str) -> str:
        """根据模式选择提示词"""
        if mode == "bailongma":
            return PROMPT_BAILONGMA
        elif mode == "todo":
            return PROMPT_TODO
        elif mode == "search":
            return PROMPT_SEARCH
        return PROMPT_CHAT

    def _build_messages(self, message: str, history: list, mode: str, session_id: str = "default") -> list:
        """构建消息列表，注入模式提示词和会话状态"""
        prompt = self._get_prompt(mode)
        state = get_session(session_id)

        # 加上会话状态片段
        state_fragment = state.to_prompt_fragment()
        if state_fragment:
            prompt += state_fragment

        msgs = [{"role": "system", "content": prompt}]

        # 加上历史（仅保留最近的消息避免上下文超长）
        max_history = 10 if mode == "bailongma" else 20
        for h in history[-max_history:]:
            msgs.append(h)

        msgs.append({"role": "user", "content": message})
        return msgs

    async def _forward_to_bailongma(self, message: str) -> AsyncGenerator:
        """把消息直接转发给白龙马，不走 LLM"""
        import urllib.request, json, time

        # 去掉"跟白龙马说""让白龙马"等前缀
        clean = re.sub(r"^(跟白龙马说|让白龙马|传给白龙马|叫白龙马|问白龙马|告诉白龙马|对白龙马说)\s*", "", message).strip()
        if not clean:
            clean = message

        yield {"type": "token", "content": "🤖 正在转发给白龙马...\n\n"}

        try:
            data = json.dumps({"content": clean, "channel": "API"}).encode()
            req = urllib.request.Request(
                "http://127.0.0.1:3722/message",
                data=data, headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())

            conv_id = result.get("conversation_id")
            if conv_id:
                for _ in range(25):
                    time.sleep(1)
                    try:
                        req2 = urllib.request.Request(
                            "http://127.0.0.1:3722/conversations",
                            headers={"Accept": "application/json"},
                        )
                        with urllib.request.urlopen(req2, timeout=5) as resp2:
                            msgs = json.loads(resp2.read())

                        # 找新增的白龙马回复，合并多段
                        for m in reversed(msgs):
                            role = (m.get("role") or "").lower()
                            if role in ("jarvis", "assistant") and m.get("content"):
                                reply = m["content"]
                                yield {"type": "token", "content": reply}
                                yield {"type": "end", "data": {
                                    "role": "assistant", "content": reply,
                                    "tool_calls_log": [{"name": "call_bailongma", "result": {"reply": reply}}]
                                }}
                                return
                    except:
                        pass

            yield {"type": "token", "content": "（白龙马暂无回复）"}
            yield {"type": "end", "data": {"role": "assistant", "content": "已转发给白龙马", "tool_calls_log": []}}

        except Exception as e:
            err = f"白龙马连接失败: {e}"
            yield {"type": "token", "content": err}
            yield {"type": "end", "data": {"role": "assistant", "content": err, "tool_calls_log": [], "error": True}}

    async def process_message(self, message, session_id, history=None):
        full = ""
        async for e in self._stream(message, session_id, history or []):
            if e["type"] == "token":
                full += e["content"]
            elif e["type"] == "end":
                return e["data"]
            elif e["type"] == "error":
                return self._build_error_response(e["content"])
        return self._build_error_response("AI 未返回有效回复")

    async def process_message_stream(self, message, session_id, history=None):
        async for e in self._stream(message, session_id, history or []):
            yield e

    async def _stream(self, message, session_id, history):
        # 1. 意图路由分类
        mode = classify_intent(message, session_id)
        logger.info(f"[路由] session={session_id} mode={mode} msg={message[:50]}")

        # 2. BaiLongma 模式：直接转发，不走 LLM
        if mode == "bailongma":
            async for e in self._forward_to_bailongma(message):
                yield e
            return

        # 3. 构建提示词
        messages = self._build_messages(message, history or [], mode, session_id)
        tool_log = []

        for rnd in range(self.max_rounds):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, messages=messages,
                    tools=self._tools or None, tool_choice="auto" if self._tools else None,
                    temperature=0.7, stream=True,
                )
            except Exception as e:
                logger.error(f"LLM 失败: {e}")
                yield {"type": "error", "content": f"AI 调用失败: {str(e)}"}
                return

            content_parts, reasoning_parts = [], []
            tc_id, tc_name, tc_args = None, None, ""

            for chunk in resp:
                d = chunk.choices[0].delta if chunk.choices else None
                if not d:
                    continue
                rc = getattr(d, 'reasoning_content', None)
                if rc:
                    reasoning_parts.append(rc)
                if d.content:
                    content_parts.append(d.content)
                    yield {"type": "token", "content": d.content}
                if d.tool_calls:
                    tc = d.tool_calls[0]
                    if tc.id:
                        tc_id, tc_name = tc.id, (tc.function.name if tc.function else None)
                        tc_args = tc.function.arguments or ""
                    elif tc.function and tc.function.arguments:
                        tc_args += tc.function.arguments

            full = "".join(content_parts)
            reasoning = "".join(reasoning_parts)

            if not tc_id:
                yield {"type": "end", "data": {
                    "role": "assistant", "content": _strip_markdown(full),
                    "tool_calls_log": tool_log
                }}
                return

            yield {"type": "tool_start", "name": tc_name, "args_str": tc_args}
            try:
                parsed = json.loads(tc_args) if tc_args else {}
            except:
                parsed = {}
            logger.info(f"工具: {tc_name}({parsed})")
            result = await tool_registry.execute(tc_name, parsed)
            tool_log.append({"name": tc_name, "args": parsed, "result": result})
            yield {"type": "tool_result", "name": tc_name, "result_str": json.dumps(result, ensure_ascii=False)}

            if full:
                messages.append({"role": "assistant", "content": full})
            tcl = [{"id": tc_id, "type": "function", "function": {"name": tc_name, "arguments": tc_args}}]
            msg = {"role": "assistant", "content": full or None, "tool_calls": tcl}
            if reasoning:
                msg["reasoning_content"] = reasoning
            messages.append(msg)
            messages.append({
                "role": "tool", "tool_call_id": tc_id,
                "content": json.dumps(result, ensure_ascii=False)
            })

        # 超过最大轮数时总结
        messages.append({"role": "user", "content": "总结你做的事"})
        try:
            final = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, stream=True
            )
            for c in final:
                if c.choices and c.choices[0].delta.content:
                    yield {"type": "token", "content": c.choices[0].delta.content}
        except:
            pass
        yield {"type": "end", "data": {
            "role": "assistant", "content": "处理完了",
            "tool_calls_log": tool_log, "truncated": True
        }}

    def _build_error_response(self, text):
        return {"role": "assistant", "content": text, "tool_calls_log": [], "error": True}
