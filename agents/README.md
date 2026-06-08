# agents — LLM Agent 模块

本目录实现束流数据分析的核心 Agent，负责与 LLM 交互、编排工具调用、管理对话历史。

## 文件说明

| 文件 | 说明 |
|------|------|
| `llm_agent.py` | `BeamDataAgent` 与 `StreamingBeamDataAgent` 实现 |
| `tool_logger.py` | 工具调用日志记录（写入 `logs/`） |
| `__init__.py` | 导出 `BeamDataAgent`、`StreamingBeamDataAgent` |

## 核心类

### BeamDataAgent

- 通过 OpenAI 兼容 API 调用 Qwen 模型
- 使用 Function Calling 自动选择并执行 `tools/` 中的 11 个工具
- 支持多轮对话与上下文记忆
- `chat()` 返回 `{ response, images }`
- `chat_with_events()` 以 SSE 事件流推送工具调用进度（供 Web 使用）

### StreamingBeamDataAgent

- 在 `BeamDataAgent` 基础上支持流式文本输出
- 通过 `main.py --stream` 使用

## 使用示例

```python
from agents import BeamDataAgent
from config import Config

config = Config.get_api_config()
agent = BeamDataAgent(**config)

result = agent.chat("查询2025年8月31日两点到三点的束流数据")
print(result["response"])

agent.reset_conversation()
```

## 依赖关系

```
agents/llm_agent.py
  ├── tools.TOOLS / TOOL_FUNCTIONS
  └── agents.tool_logger.ToolCallLogger → logs/
```

## 相关入口

- 命令行：[main.py](../main.py)
- Web 服务：[app.py](../app.py)
- OpenClaw 配置：[.openclaw.json](../.openclaw.json) 中 `agent_impl_file` 指向本模块
