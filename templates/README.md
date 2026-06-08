# templates — Web 页面模板

Flask Jinja2 模板目录。

## 文件

| 文件 | 说明 |
|------|------|
| `index.html` | 束流数据智能分析系统主页面 |

## 页面结构

- 顶部：系统标题、状态指示、数据集信息
- 中部：聊天消息区域（欢迎卡片 + 对话历史）
- 底部：输入框与发送按钮

## 前端依赖

- 样式：[static/css/style.css](../static/css/style.css)
- 脚本：[static/js/app.js](../static/js/app.js)
- 图标：Font Awesome CDN
- 字体：Inter (Google Fonts)

## 路由

由 [app.py](../app.py) 中 `@app.route('/')` 渲染：

```python
return render_template('index.html')
```
