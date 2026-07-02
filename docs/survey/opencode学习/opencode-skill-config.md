# OpenCode Skill 配置与发现机制

> 撰写日期: 2026-07-02
> 来源: obra/superpowers + anthropics/skills 社区技能导入实践

---

## 1. 背景：为什么 31 个技能已复制但无法加载

将社区技能复制到项目 `.agent/skills/` 后，OpenCode 并未自动发现它们。根本原因：
OpenCode 的 Skill Server 在**启动时**构建索引，运行期间不会重新扫描文件系统。

**证据**：Skill Server index.json 只返回 2 个旧技能：

```bash
$ curl -s http://127.0.0.1:39847/index.json
{"skills":[{"name":"security-research","files":["SKILL.md"]},{"name":"security-review","files":["SKILL.md"]}]}
```

---

## 2. OpenCode Skill 发现全景（8 个扫描源）

从 `oh-my-openagent` 插件源码（打包在 `~/.config/opencode/node_modules/`）可以还原出完整的 skill 发现管道。OpenCode 通过 **`discoverAgentSkills`** 主编排器从 8 个来源并行扫描并合并：

| # | 来源 | 扫描路径 | 作用域 |
|---|------|---------|--------|
| 1 | Config Sources | `opencode.json` → `skills.sources[]` | 配置 |
| 2 | Config Paths/URLs | `opencode.json` → `skills.paths[]` / `skills.urls[]` | 配置 |
| 3 | User Claude Skills | `~/.claude/skills/` | 用户全局 |
| 4 | Project Claude Skills | 从 CWD 向上查找 `.claude/skills/` | 项目级 |
| 5 | Project Agents Skills | 从 CWD 向上查找 **`.agents/skills/`**（注意复数 `s`） | 项目级 |
| 6 | Global Agent Skills | `~/.agents/skills/` | 用户全局 |
| 7 | OpenCode Global Skills | `~/.config/opencode/skills/` + `~/.config/opencode/skill/` | 全局 |
| 8 | OpenCode Project Skills | 从 CWD 向上查找 `.opencode/skills/` + `.opencode/skill/` | 项目级 |

**项目 `.agent/skills/` 不在任何默认扫描路径内**（OpenCode 扫描的是 `.agents/skills/` —— 多了个 `s`）。

### 环境变量

| 变量 | 说明 |
|------|------|
| `OPENCODE_DISABLE_EXTERNAL_SKILLS=1` | 完全禁用外部 skill 扫描 |
| `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` | 跳过 `~/.claude/` 和 `~/.agents/` 扫描 |
| `OPENCODE_CONFIG_DIR` | 自定义配置目录（默认 `~/.config/opencode/`） |
| `XDG_CONFIG_HOME` | 备选配置目录（默认 `~/.config/`） |

---

## 3. 解决方案

### 方案 A：通过 `opencode.json` 配置 `skills.paths`（**已实施**）

在 `~/.config/opencode/opencode.json` 中添加：

```json
{
  "skills": {
    "paths": [".agent/skills"]
  }
}
```

`paths` 中的相对路径会相对于项目目录（CWD）解析。绝对路径和 `~/` 路径也被支持。

**需重启 OpenCode 生效。**

### 方案 B：复制到 `~/.cache/opencode/skills/`

全局 cache 目录也会在启动时被扫描。若文件已在此目录中，重启后即可被发现。

### 方案 C：使用 `.opencode/skills/` 目录

OpenCode 原生支持项目级 `.opencode/skills/`（来源 #8），无需额外配置。将技能移至此目录后重启即可。

### 方案 D：使用 `OPENCODE_DISABLE_EXTERNAL_SKILLS` 调试

若需临时禁用外部 skill 扫描排查问题：
```bash
OPENCODE_DISABLE_EXTERNAL_SKILLS=1 opencode
```

---

## 4. SKILL.md 格式参考

### 文件结构

```
skill-name/
├── SKILL.md           # 必需：YAML frontmatter + Markdown 指令
├── scripts/           # 可选：可执行代码
├── references/        # 可选：按需加载的文档
├── assets/            # 可选：静态资源（模板、图标、数据）
└── mcp.json           # 可选：Claude Desktop 格式的 MCP 服务器配置
```

### YAML Frontmatter 字段

**必需字段：**

| 字段 | 类型 | 约束 |
|------|------|------|
| `name` | string | 1-64 字符。小写字母、数字、连字符。必须匹配父目录名。 |
| `description` | string | 1-1024 字符。描述技能**做什么**以及**何时触发**。 |

**可选字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `license` | string | 许可证 |
| `compatibility` | string | 兼容性要求 |
| `allowed-tools` | string/list | 允许的工具列表（空格分隔字符串或 YAML 列表） |
| `metadata` | dict[str,str] | 任意键值对 |
| `disable-model-invocation` | bool | 设为 true 则从 `<available-skills>` 隐藏 |
| `user-invocable` | bool | 默认 true。设为 false 则标记为不可用户调用 |
| `context` | string | 上下文模式（如 `fork`, `continue`） |
| `agent` | string | 兼容的 agent 类型（如 `general-purpose`, `coding`） |
| `argument-hint` | string | 斜杠命令自动补全提示 |
| `tools` | list | `[{type: "python", import_path: "module:function"}]` |

### 最小有效 SKILL.md 示例

```yaml
---
name: my-skill
description: "当用户说 X 时做 Y。触发词：'do X', 'run X'。"
---
# skill 主体内容
## 使用说明
...
```

### 完整实例

```yaml
---
name: code-reviewer
description: "Review code changes for quality and security. Triggers: 'review this', 'code review'."
license: MIT
allowed-tools: "bash read grep lsp_diagnostics"
metadata:
  author: team
  version: "1.0"
disable-model-invocation: false
user-invocable: true
context: fork
agent: coding
---
# Code Review Skill

## 使用流程
...
```

---

## 5. 推荐的项目技能目录结构

**推荐方案：使用 `.agent/skills/` + `skills.paths` 配置**

```
JanusAgent/
├── .agent/
│   ├── AGENT.md
│   ├── context/
│   ├── rules/
│   ├── memory/
│   └── skills/                  ← 项目级技能（已配置、待重启）
│       ├── brainstorming/       ← 来自 obra/superpowers
│       ├── frontend-design/     ← 来自 anthropics/skills
│       ├── my-custom-skill/     ← 自定义技能
│       └── ...
├── docs/survey/opencode学习/     ← 本文档
└── .config/opencode/opencode.json  ← 已添加 skills.paths 配置
```

**区别总结：**

| 位置 | 作用域 | 版本控制 | 配置方式 | 生效条件 |
|------|--------|---------|---------|---------|
| `.agent/skills/` | 项目级 | ✅ git 管理 | `skills.paths` | 重启后 |
| `~/.cache/opencode/skills/` | 全局 | ❌ cache 目录 | 自动扫描 | 重启后 |
| `.opencode/skills/` | 项目级 | ✅ git 管理 | 自动扫描（原生） | 重启后 |

---

## 6. 关键源文件索引

| 文件 | 说明 |
|------|------|
| `~/.config/opencode/opencode.json` | 主配置文件（已添加 `skills.paths`） |
| `~/.config/opencode/oh-my-openagent.json` | oh-my-openagent 插件配置 |
| `~/.config/opencode/dcp.jsonc` | 动态上下文剪枝配置 |
| `~/.local/share/opencode/log/` | 运行时日志（skill-discovery 在其中） |
| `~/.cache/opencode/skills/` | 全局 skill 缓存目录 |
| `~/.local/state/opencode/kv.json` | 键值存储（UI 偏好等） |
| `~/bin/opencode` | 二进制（内嵌 skill 发现代码） |
| `.agent/AGENT.md` | 项目 AGENT 入口文档 |
| `.agent/skills/` | 项目级技能目录 |

---

## 7. 验证技能是否加载成功

重启 OpenCode 后，可通过以下方式验证：

```bash
# 检查 skill index
curl -s http://127.0.0.1:<PORT>/index.json

# 日志中查看 skill-discovery 服务的初始化信息
grep "skill" ~/.local/share/opencode/log/2026-07-*.log

# 在会话中检查 <available-skills> XML 块
# 新的 load_skills=["skill-name"] 也应能正确加载
```
