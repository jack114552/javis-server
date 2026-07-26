# Javis 🔧

个人 AI 助手 — 全端 + 自主决策 Agent

一个跑在服务器上的 AI 智能体，通过手机通知感知事件，**自主决策**并执行工具操作（写入待办、设置提醒、查信息），通过语音/文字推送到你的手机和电脑。

## 快速开始

### 1. 配置

```bash
cd server
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动

```bash
python main.py
```

浏览器打开 `http://localhost:8080` 开始对话。

## 架构

```
┌─ 手机(Flutter) ─┐    ┌─ 服务器(Python) ──────────┐    ┌─ 桌面(Web) ───┐
│  通知轮询        │───►│  AI 引擎 (Function Calling)│◄──►│  网页界面     │
│  语音播报        │    │  ▶ 待办系统               │    │  待办面板     │
│  对话界面        │◄───│  ▶ 提醒引擎               │    │  语音播报     │
└─────────────────┘    │  ▶ 长期记忆               │    └──────────────┘
                        │  ▶ TTS 合成               │
                        └───────────────────────────┘
```

## API 概览

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 对话接口 |
| `/api/ws` | WebSocket | 实时对话 |
| `/api/notifications` | POST | 接收手机通知 |
| `/api/todos` | GET/POST | 待办列表/创建 |
| `/api/todos/{id}` | PATCH/DELETE | 更新/删除待办 |
| `/api/system/health` | GET | 健康检查 |

## 工具清单（AI 可自主调用）

- `add_todo` / `complete_todo` / `delete_todo` — 待办管理
- `set_reminder` / `delete_reminder` — 提醒设置
- `search_memory` / `save_memory` — 长期记忆
- `get_current_time` — 获取当前时间
- `web_search` — 联网搜索（预留）

## 开发

```bash
# 开发模式（热重载）
python main.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

详见 [DEVLOG.md](../DEVLOG.md) 了解架构决策和已知坑点。
