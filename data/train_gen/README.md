# data/train_gen — 训练数据生成

存放 LLM 工具调用微调样本的生成产物。

## 生成流程

由 `scripts/` 下三步脚本依次执行：

```bash
# 1. 生成 question + tool_call
python scripts/step1_generate_questions.py

# 2. 执行工具获取 tool_response
python scripts/step2_fetch_tool_responses.py

# 3. 模拟助手最终回复
python scripts/step3_simulate_assistant.py
```

## 样本类别

| 类别 | 说明 |
|------|------|
| `single_tool` | 单工具调用 |
| `tool_chain` | 多工具链式调用 |
| `no_tool` | 无需工具的通用对话 |

## 典型文件

| 文件 | 说明 |
|------|------|
| `questions.jsonl` | 阶段 1 输出：问题 + 工具调用 |
| `with_responses.jsonl` | 阶段 2 输出：附加工具返回 |
| `final.jsonl` | 阶段 3 输出：完整训练样本 |
| `test_samples.jsonl` | 测试/验证样本 |

## JSONL 记录格式

```json
{
  "question": "用户问题",
  "tool_call": { "name": "query_beam_data", "arguments": {...} },
  "tool_response": { "success": true, ... },
  "assistant": "助手最终回复",
  "category": "single_tool"
}
```

## 相关脚本

- [scripts/step1_generate_questions.py](../../scripts/step1_generate_questions.py)
- [scripts/step2_fetch_tool_responses.py](../../scripts/step2_fetch_tool_responses.py)
- [scripts/step3_simulate_assistant.py](../../scripts/step3_simulate_assistant.py)
- [scripts/test_samples_to_beam_format.py](../../scripts/test_samples_to_beam_format.py) — 格式转换
