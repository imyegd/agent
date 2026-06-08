# docs — 文档与图表

存放项目文档、演示材料和实验对比图表。

## 文件说明

| 文件 | 说明 |
|------|------|
| `openclaw_comparison_bars.png` | OpenClaw vs 直接调用效率对比柱状图 |
| `openclaw_comparison_table.png` | 效率对比汇总表 |
| `ppt_example_feature_explain.json` | 特征解释演示用例（JSON） |
| `ppt_example_feature_explain.png` | 特征解释演示截图 |

## 图表生成

OpenClaw 对比图由以下脚本生成：

```bash
python scripts/plot_openclaw_comparison.py
```

数据来源：`trail/openclaw/` 和 `trail/data/` 下的效率测试结果 JSON。

## 说明

本目录仅存放静态文档资源，不含可执行代码。项目主文档见根目录 [README.md](../README.md)。
