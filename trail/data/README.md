# trail/data — 测试结果数据

存放效率测试和对比实验的 JSON 结果文件。

## 文件命名

```
efficiency_results_YYYYMMDD_HHMMSS.json
skills_direct_efficiency_YYYYMMDD_HHMMSS.json
skills_openclaw_efficiency_YYYYMMDD_HHMMSS.json
```

## 记录内容

典型字段：

```json
{
  "test_name": "beam-data-query",
  "tool": "query_beam_data",
  "duration_ms": 45.2,
  "success": true,
  "prompt_tokens": 0,
  "completion_tokens": 0
}
```

## 生成方式

由 `trail/run_*.py` 脚本运行后自动写入。

## 可视化

```bash
python scripts/plot_openclaw_comparison.py
```

读取本目录和 `trail/openclaw/` 下的结果，生成对比图到 `docs/`。
