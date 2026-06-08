# scripts — 辅助脚本

项目维护、训练数据生成、统计分析和可视化脚本。

## 训练数据生成（三步流水线）

| 脚本 | 说明 |
|------|------|
| `step1_generate_questions.py` | 生成 question + tool_call → `data/train_gen/questions.jsonl` |
| `step2_fetch_tool_responses.py` | 执行工具获取 tool_response |
| `step3_simulate_assistant.py` | 模拟助手最终回复，输出完整训练样本 |

```bash
python scripts/step1_generate_questions.py
python scripts/step2_fetch_tool_responses.py
python scripts/step3_simulate_assistant.py
```

## 其他脚本

| 脚本 | 说明 |
|------|------|
| `generate_tool_train_data.py` | 训练数据生成（一体化版本） |
| `test_samples_to_beam_format.py` | 将样本转换为 Beam 微调格式 |
| `count_tool_calls.py` | 统计 `logs/` 中工具调用情况 |
| `plot_openclaw_comparison.py` | 生成 OpenClaw 效率对比图 → `docs/` |

## 运行方式

所有脚本从项目根目录执行：

```bash
cd D:\code\graduate\llm
python scripts/<脚本名>.py
```

脚本内部已将项目根目录加入 `sys.path`。
