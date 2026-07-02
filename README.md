# JanusAgent

**面向私人的双面智能体框架 — 理性与感性，统一于一个框架。**

JanusAgent 是一个可定制的双面个人智能体框架，基于 **AgentPool** 构建，同时运行两个 AI 智能体：

- **Quant Agent** — 理性之面：量化交易分析、市场数据、策略与回测
- **Companion Agent** — 感性之面：情感陪伴、对话交互、记忆与共情

两者共享同一个 AgentPool 编排层，通过统一的 YAML 配置管理，并可跨多种协议暴露（ACP、AG-UI、MCP、OpenCode）。

---

## 项目结构

```
JanusAgent/
├── main.py                        # 框架入口
├── pyproject.toml                 # UV 工作区根配置
├── ruff.toml                      # Ruff 规则
├── .pre-commit-config.yaml        # Git hooks
├── uv.lock                        # 依赖锁文件
│
├── packages/
│   ├── agent-core/                # 核心抽象层：Agent 内核、生命周期、插件接口
│   ├── agentpool/                 # AgentPool 编排中枢（多协议桥接）
│   ├── quant-agent/               # 量化交易智能体
│   └── companion-agent/           # 情感陪伴智能体
│
├── .agent/                        # AI 智能体配置（上下文、规则、决策日志、技能）
├── .omo/                          # 任务编排（计划、证据、备忘）
├── docs/                          # 技术调研与文档
└── openspec/                      # 规格驱动的变更管理
```

## 架构

```
┌──────────────────────────────────────────────┐
│                 JanusAgent                    │
│        (main.py - framework orchestrator)     │
├──────────────────────────────────────────────┤
│                                               │
│  ┌──────────────┐    ┌──────────────────┐     │
│  │  Quant Agent  │    │ Companion Agent  │     │
│  │  (理性之面)    │    │  (感性之面)       │     │
│  └──────┬───────┘    └────────┬─────────┘     │
│         │                     │                │
│         └──────────┬──────────┘                │
│                    │                           │
│           ┌────────▼────────┐                  │
│           │   AgentPool     │                  │
│           │  (编排中枢)      │                  │
│           │  ACP/AG-UI      │                  │
│           │  MCP/OpenCode   │                  │
│           └─────────────────┘                  │
│                                                │
└────────────────────────────────────────────────┘
```

## 子包说明

| 包 | 描述 |
|---|---|
| **agent-core** | 核心抽象层 — Agent 内核基类、生命周期管理、插件化接口 |
| **agentpool** | 编排中枢 — YAML 驱动的多智能体编排，桥接 ACP/AG-UI/MCP/OpenCode 协议 |
| **quant-agent** | 量化交易智能体 — 市场数据（K线）、策略定义（回测框架） |
| **companion-agent** | 情感陪伴智能体 — 对话管理、记忆存储、多轮交互 |

## 快速开始

```bash
# 安装依赖
uv sync --all-extras

# 启动框架
python main.py

# 代码检查
ruff check .

# 代码格式化
ruff format .

# 运行测试
pytest
```

## 开发栈

| 组件 | 技术 |
|---|---|
| 语言 | Python 3.12+ |
| 包管理 | `uv` (workspace mode) |
| 代码检查 | `ruff` |
| 格式化 | `ruff format` |
| Pre-commit | `pre-commit` |
| 测试 | `pytest` |
| 文档字符串 | Google 风格 |

## License

MIT
