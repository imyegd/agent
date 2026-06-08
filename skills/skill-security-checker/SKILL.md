---
name: skill-security-checker
description: 手动审查第三方技能的安全性，检查 SKILL.md、脚本、依赖和风险点
---

# Skill 安全审查指南

## 审查清单

### 1. SKILL.md 内容审查

**必须检查的文件**: `{skill-folder}/SKILL.md`

- [ ] **Frontmatter 格式正确**
  - name/description 必填
  - metadata 部分无恶意配置
  
- [ ] **描述与功能匹配**
  - description 清晰说明用途
  - 没有夸大或模糊的描述
  
- [ ] **权限要求合理**
  - `metadata.openclaw.requires` 中声明的 bins/env/config 是否符合功能需求
  - 没有过度请求敏感环境变量（如 API_KEY、密码等）

### 2. 脚本执行风险

**检查所有 .sh / .bat / .ps1 / .py 文件**

```bash
# 查看技能目录下的所有可执行脚本
ls skills/<skill-name>/

# 检查是否包含危险命令
grep -E "(curl|wget|rm|eval|exec|chmod|sudo)" skills/<skill-name>/*.sh
```

**危险模式**:
- ❌ 自动下载安装未知二进制文件
- ❌ 删除系统文件 (`rm -rf /`)
- ❌ 修改系统配置
- ❌ 发送数据到未知外部地址
- ❌ 使用 `eval` 或动态执行用户输入

### 3. 依赖审查

**检查 package.json / requirements.txt / go.mod 等**

- [ ] 依赖来源可信（npmjs.org, pypi.org 等官方源）
- [ ] 没有奇怪的私有 registry
- [ ] 版本号固定（避免依赖被篡改）

### 4. 代码静态检查

**如果有源码文件 (.js/.ts/.py)**

```bash
# 简单的恶意代码检测
grep -r "eval\|exec\|require('child_process')\|os.system" skills/<skill-name>/
```

### 5. 外部链接检查

**检查所有 URL 链接**

- [ ] 链接指向可信域名
- [ ] 没有短链接或重定向陷阱
- [ ] API 端点符合预期

## 快速检查命令

```powershell
# 1. 列出技能文件夹结构
ls C:\Users\jinta\.openclaw\workspace\skills\<skill-name>\

# 2. 读取 SKILL.md 查看声明的功能
cat C:\Users\jinta\.openclaw\workspace\skills\<skill-name>\SKILL.md

# 3. 搜索危险命令
Select-String -Path "C:\Users\jinta\.openclaw\workspace\skills\<skill-name>\*" -Pattern "curl|wget|rm -rf|eval|exec"

# 4. 查看是否有隐藏文件
ls -la C:\Users\jinta\.openclaw\workspace\skills\<skill-name>\
```

## 风险等级判定

| 等级 | 标志 | 处理建议 |
|------|------|----------|
| 🔴 高风险 | 包含可疑脚本、请求敏感 env、修改系统 | **不要安装** |
| 🟡 中风险 | 有外部调用但不明确、依赖不常见 | 人工审计后再决定 |
| 🟢 低风险 | 只有文档、简单脚本、功能透明 | 可以安全使用 |

## 推荐实践

1. **优先使用官方/知名来源的技能**（如 OpenClaw 内置、ClawHub 高星技能）
2. **安装前 Always Read the Code** - 即使是小脚本也要看
3. **在测试环境先试用** - 确认无异常后再在生产环境使用
4. **定期审计已安装的技能** - 检查是否有未预期的行为

## OpenClaw 内置安全检查

你的 OpenClaw 已有 `healthcheck` 技能可用于系统安全检查：

```bash
openclaw skills check  # 检查哪些技能就绪
openclaw skills list   # 列出所有可用技能
```
