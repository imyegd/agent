# static — Web 静态资源

Flask Web 应用的前端静态文件。

## 目录结构

```
static/
├── css/
│   └── style.css      # 主样式表
└── js/
    └── app.js         # 前端交互逻辑
```

## 功能

- 聊天界面渲染与消息展示
- 调用 `/api/chat` 和 `/api/chat/stream` 接口
- 展示工具生成的图表（`/output/` 路径）
- 加载数据集元信息（`/api/data/info`）

## 相关文件

- 页面模板：[templates/index.html](../templates/index.html)
- 后端服务：[app.py](../app.py)

## 启动

```bash
python app.py
# 访问 http://localhost:5000
```
