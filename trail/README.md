# trail — 测试与追踪

效率测试、OpenClaw 对比实验和会话追踪工具。

## 主要脚本

| 脚本 | 说明 |
|------|------|
| `run_efficiency_test.py` | Agent 端到端效率测试（token、耗时、工具调用） |
| `run_openclaw_efficiency_test.py` | OpenClaw vs 直接调用对比 |
| `run_skills_efficiency_test.py` | 直接调用各工具函数的效率测试 |

## 子目录

| 目录 | 说明 |
|------|------|
| [openclaw/](openclaw/README.md) | OpenClaw 会话日志解析与追踪 |
| [data/](data/README.md) | 效率测试结果 JSON |

## 快速使用

```bash
# Agent 端到端测试
python trail/run_efficiency_test.py

# 工具直调效率测试
python trail/run_skills_efficiency_test.py

# OpenClaw 今日报告
powershell trail/openclaw/daily_report.ps1
```

## 输出

测试结果保存为 JSON（含时间戳），对比图由 [scripts/plot_openclaw_comparison.py](../scripts/plot_openclaw_comparison.py) 生成到 `docs/`。
