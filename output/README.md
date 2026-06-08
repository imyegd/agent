# output — 运行时输出

存放工具执行过程中生成的图表等文件。

## 内容

主要由 `plot_beam_data` 工具生成束流时序图：

```
beam_YYYYMMDD_HHMMSS_mmm.png
```

## 访问方式

- **Web**：通过 `app.py` 的 `/output/<filename>` 路由提供静态访问
- **本地**：Agent 返回结果中的 `plot_path` / `images` 字段指向此目录

## 注意事项

- 目录在 `app.py` 启动时自动创建（`os.makedirs('output', exist_ok=True)`）
- 历史图表可定期清理，不影响系统运行
- 部分图表也可能被复制到 [docs/](../docs/) 用于文档展示
