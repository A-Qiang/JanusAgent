# `.agent` / `.agents` 目录背景与溯源

> 本文档追溯 AI 编码代理项目配置标准（`AGENT.md`、`AGENTS.md`、`.agent/`、`.agents/`）的完整演进历史，包含每个关键节点的提出者、时间、动机和验证来源。

---

## 1. 背景：碎片化问题

2025 年中期，AI 编码工具爆发式增长，每个工具都发明了自己的项目配置文件：

| 工具 | 配置文件 |
|---|---|
| Claude Code (Anthropic) | `CLAUDE.md` |
| Cursor | `.cursorrules` 或 `.cursor/rules/` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Windsurf | `.windsurfrules` |
| Gemini CLI (Google) | `GEMINI.md` |
| Zed | `.zed/` |
| Kiro | `.kiro/steering/` |
| JetBrains Junie | `.junie/guidelines.md` |
| Trae | `.trae/rules/` |
| Aider | `.aider.conf.yml` |

开发者被迫维护多个配置文件，或者把大量指令塞进 `README.md` 中。这催生了统一标准的呼声。

**引爆点**: 2025年5月16日，Aiden Bai（@aidenybai）在 X 上发了一个 meme 吐槽"9 个竞争标准"，引发广泛讨论。

---

## 2. `AGENT.md`（单文件，无 S）— 最早的标准

### 提出者

- **组织**: Sourcegraph, Inc.（其 AI 编码工具 Amp）
- **个人**: Quinn Slack（@sqs，Sourcegraph CEO / Amp 创始人）、Geoffrey Huntley
- **规范作者**: Geoffrey Huntley（Sourcegraph 员工）

### 时间线

| 日期 | 事件 |
|---|---|
| **2025-05-07** | Sourcegraph 的 Amp 首次原生支持 `AGENT.md` |
| **2025-05-16** | Quinn Slack 公开提议社区统一到 `AGENT.md`，表态愿意妥协 |
| **2025-05-17** | OpenAI 的 Alexander Embiricos（@embirico）回应，同意需要统一文件名，开始协作 |
| **2025-07** | Geoffrey Huntley 发布正式规范文档，仓库 [agentmd/agent.md](https://github.com/agentmd/agent.md) |
| **2025-07-07** | Amp 支持多级 `AGENT.md` 文件（根目录 + 子目录 + `~/.config/AGENT.md`） |

### 核心主张

一个 Markdown 文件放在项目根目录，作为 AI 代理的"README"。所有工具都读取同个文件，不再碎片化。

### 验证来源

- 规范仓库: https://github.com/agentmd/agent.md — 明确标注 Author: Geoffrey Huntley, Organization: Sourcegraph, Inc.
- Amp 文档: https://ampcode.com/manual#AGENT.md

---

## 3. `AGENTS.md`（带 S 的单文件）— 社区统一标准

### 提出者

- **主导方**: OpenAI（Codex 团队）
- **联合支持**: Google（Jules）、Sourcegraph（Amp）、Cursor、Factory AI
- **当前托管**: Linux Foundation 下属 **Agentic AI Foundation**

### 时间线

| 日期 | 事件 |
|---|---|
| **2025-07-16** | OpenAI 的 Alexander Embiricos 宣布 OpenAI 已获得 `agents.md` 域名，将搭建最佳实践站点 |
| **2025-08-19** | OpenAI 创建仓库 [agentsmd/agents.md](https://github.com/openai/agents.md)（现 22K+ stars），选择 `AGENTS.md`（带 S）作为折中标准名 |
| **2025-08-20** | Hacker News 发布，获 837 分 |
| **2025-08 起** | Google Jules、Codex、OpenCode、Gemini CLI、Factory AI 等陆续加入支持 |
| **2025-11** | 研究显示已有 2,500+ 仓库使用 AGENTS.md |
| **2026-04** | 标准移交 **Linux Foundation / Agentic AI Foundation** 托管，60,000+ 开源项目采用 |

### 与 `AGENT.md` 的关系

`AGENT.md`（Sourcegraf/Amp 提出）和 `AGENTS.md`（OpenAI 推动）本质是同一概念的两个名字。社区最终选择了 `AGENTS.md`（带 S）作为标准，Sourcegraph 也表态支持并保持向后兼容。

**Anthropic（Claude Code）至今未正式支持 AGENTS.md**，是主要厂商中唯一的"保留者"。

### 验证来源

- 主仓库: https://github.com/openai/agents.md
- 官网: https://agents.md/
- InfoQ 报道: https://www.infoq.com/news/2025/08/agents-md/
- Linux Foundation 托管: 见 Issue #135 中维护者确认

---

## 4. `.agent/` 目录（无 S，目录形式）— 由 Issue #71 提出

### 提出者

- **GitHub 用户**: **haoranba**（@haoranba）
- **提出位置**: agentsmd/agents.md 仓库的 Issue #71

### 时间线

| 日期 | 事件 |
|---|---|
| **2025-09-25** | haoranba 提交 Issue #71，标题 *"Proposal: Standardize a .agent Directory for Comprehensive Project Context"* |
| 后续 | 该 issue 被多次引用（Issue #135、#179 等），成为目录结构方案的奠基性讨论 |

### 提议结构

```
├── AGENT.md               # 核心行为指导
└── .agent/
    ├── spec/              # 项目"蓝图"：PRD、设计文档、架构定义
    │   ├── requirement.md
    │   ├── design.md
    │   └── tasks.md
    ├── knowledge/         # 项目"百科全书"：稳定的全局知识
    │   ├── architecture.md
    │   └── domain.md
    ├── links/             # 项目"通讯录"：管理外部资源链接
    └── plans/             # 短期、按任务的实现计划
```

### 核心动机

`AGENT.md` 单文件在小项目中够用，但复杂项目需要更结构化的上下文组织。"Directory as Context"（目录即上下文）策略——把上下文拆分到多个文件中，按需加载，避免单文件膨胀。

### 验证来源

- Issue #71: https://github.com/agentsmd/agents.md/issues/71
- 提出者 haoranba 的 GitHub 主页: https://github.com/haoranba

---

## 5. `.agents/` 目录（带 S）— 多路并行的目录标准

在 haoranba 的 `.agent` 提案之外，还有多条并行的 `.agents` 目录标准演进：

### 5.1 最早的概念提出 — @jsit

| 日期 | 提出者 | 事件 |
|---|---|---|
| **2025-08-20** | **jsit**（@jsit） | 在 agentsmd/agents.md 仓库提交 **Issue #2**，标题 *".agents Directory Ideas"*，首次提出 `.agents` 目录概念 |
| **2025-08-20** | **jsit** | 提交 **Issue #9** *"Directory support"*，提议标准支持扫描 `.agents/` 子目录 |
| **2025-09-17** | **sangron**（@sangron） | 提交 **Issue #62** *".agents subfolder"*，正式提议增加 `.agents` 子目录支持 |

Issue #2 是**有记录的第一个提出 `.agents` 目录概念的人**——仅在 agentsmd 仓库创建后的第二天。

### 5.2 agentsfolder/spec — @burn2delete

| 日期 | 提出者 | 事件 |
|---|---|---|
| **2026-01-19** | **burn2delete**（@burn2delete） | 创建 [agentsfolder/spec](https://github.com/agentsfolder/spec) 仓库和 [agentsfolder](https://github.com/agentsfolder) 组织，发布完整的 `.agents/` 规范（AGENTS-1） |
| **2026-02-02** | burn2delete | 发布配套 CLI 工具 `agents-cli`（Rust），可将 `.agents/` 配置投射到各工具的本地格式 |

这是**第一个完整的 `.agents/` 目录规范**，定义了:
- `manifest.yaml` — 清单文件（specVersion、defaults、enabled）
- `prompts/` — base.md、project.md、snippets/
- `modes/` — 工作模式
- `policies/` — 安全策略
- `skills/` — 能力定义
- `scopes/`、`profiles/`、`schemas/`、`state/`

以及确定性解析算法（工具/CLI 覆盖 > 仓库配置 > 作用域 > 用户覆盖）。

### 5.3 dotagents — @bgreenwell

| 日期 | 提出者 | 事件 |
|---|---|---|
| **2026-01-31** | **bgreenwell**（@bgreenwell） | 发布 [dotagents](https://github.com/bgreenwell/dotagents) 标准 |

核心思想：`AGENTS.md` 作为"路由器"（入口点），`.agents/` 目录存放详细上下文。

```
AGENTS.md              # 入口 + 路由器（必需）
└── .agents/           # 推荐上下文目录
    ├── rules/         # 不变的行为准则
    ├── context/       # 静态参考数据（只读）
    ├── logs/          # 代理活动日志
    ├── memory/        # 持久项目知识（读/写）
    ├── personas/      # 专业化代理角色
    ├── skills/        # 可执行能力（agentskills.io 兼容）
    └── specs/         # 当前任务需求
```

### 5.4 ACS (Agentic Collaboration Standard) — @jackby03

| 日期 | 提出者 | 事件 |
|---|---|---|
| **2026-03-10** | **jackby03**（@jackby03） | 发布 [ACS - Agentic Collaboration Standard](https://acs.jackby03.com/) |

最完整的 `.agents/` 目录标准之一，定义了 6 个层：

```
your-project/
└── .agents/
    ├── main.yaml          # 清单
    ├── context/           # 代理需要知道的
    ├── skills/            # 代理能做的
    ├── commands/          # 可复用的单步任务
    ├── agents/            # 命名子代理（reviewer, tester 等）
    └── permissions/       # 代理被允许做什么
```

ACS 设计了 3 级渐进加载策略（Tier 1/2/3），并提供了 CLI 和 VS Code 插件。

### 5.5 Agent Spec — Oracle

| 日期 | 提出者 | 事件 |
|---|---|---|
| 2025-10 | **Oracle 公司** | 发布 [Open Agent Spec](https://github.com/oracle/agent-spec)，arXiv 论文: [2510.04173](https://arxiv.org/html/2510.04173v1) |

大厂入场的信号，表明这个方向已获得企业级认可。

---

## 6. 全景图谱

```
时间线（2025 → 2026）
═══════════════════════════════════════════════════════════

2025-05     Sourcegraph/Amp 推出 AGENT.md              ← 最早单文件标准
                ↓
2025-07     Geoffrey Huntley 发布 AGENT.md 正式规范
                ↓
2025-08-19  OpenAI 创建 agentsmd/agents.md 仓库        ← 社区标准诞生
2025-08-20  @jsit 提出 Issue #2 (.agents 目录概念)     ← 最早目录概念
2025-08-20  @jsit 提出 Issue #9 (目录支持)
                ↓
2025-09-17  @sangron 提出 Issue #62 (.agents 子文件夹)
2025-09-25  @haoranba 提出 Issue #71 (.agent 目录)     ← .agent 首次提出
                ↓
2025-10     Oracle 发布 Open Agent Spec                 ← 大厂入场
                ↓
2026-01-19  @burn2delete 发布 agentsfolder/spec        ← 首个完整 .agents/ 规范
2026-01-31  @bgreenwell 发布 dotagents 标准
                ↓
2026-03-10  @jackby03 发布 ACS 标准                    ← 最完整的目录方案
                ↓
2026-04     AGENTS.md 移交 Linux Foundation / Agentic AI Foundation

核心谱系：
  AGENT.md (单文件, Sourcegraph) ───→ AGENTS.md (单文件, OpenAI/社区) ─→ Linux Foundation
                                        │
                                        ├── .agent/  (haoranba, Issue #71)
                                        │
                                        └── .agents/ (多路演进)
                                              ├── agentsfolder/spec (burn2delete)
                                              ├── dotagents (bgreenwell)
                                              └── ACS (jackby03)
```

---

## 7. 当前生态现状

| 标准 | 形态 | 采用情况 | 维护方 |
|---|---|---|---|
| `AGENTS.md` | 单 Markdown 文件 | 60,000+ 项目 | Linux Foundation / Agentic AI Foundation |
| `AGENT.md` | 单 Markdown 文件 | Amp 用户 | Sourcegraph（向后兼容） |
| `.agent/` | 目录 | 提案阶段 | 社区讨论中 |
| `.agents/` (agentsfolder) | 目录 + 规范 | 早期 | @burn2delete |
| `.agents/` (dotagents) | 目录 + 路由器模式 | 提案阶段 | @bgreenwell |
| `.agents/` (ACS) | 目录 + 6 层 + CLI | ~1.0 发布 | @jackby03 |
| `.agent.md` | 角色定义文件 | VS Code / GitHub Copilot | Microsoft（独立概念） |

### 关键结论

1. **`AGENT.md`** 是源头，由 **Sourcegraph (Amp)** 在 2025年5月提出
2. **`AGENTS.md`** 是社区妥协的统一标准，**OpenAI + Google + Sourcegraph + Cursor + Factory** 联合推进，现由 **Linux Foundation** 托管
3. **`.agent/` 目录** 由 **@haoranba** 在 2025年9月25日的 Issue #71 中首次正式提出
4. **`.agents/` 目录** 概念最早由 **@jsit** 在 2025年8月20日的 Issue #2 中提出，后续由 **@burn2delete**（agentsfolder/spec）、**@bgreenwell**（dotagents）、**@jackby03**（ACS）分别演进出完整规范
5. 各个目录标准虽有差异，但核心理念一致：**从单文件走向目录结构，支持渐进式上下文加载（Progressive Disclosure）**
6. **Anthropic（Claude Code）** 是目前唯一未正式支持 AGENTS.md 的主要厂商

---

## 附录：关键链接

- AGENTS.md 官网: https://agents.md/
- agentsmd/agents.md 仓库: https://github.com/openai/agents.md
- agentmd/agent.md 规范: https://github.com/agentmd/agent.md
- Issue #2 (最早的 `.agents` 目录概念): https://github.com/agentsmd/agents.md/issues/2
- Issue #9 (目录支持提议): https://github.com/agentsmd/agents.md/issues/9
- Issue #62 (.agents 子文件夹): https://github.com/agentsmd/agents.md/issues/62
- Issue #71 (.agent 目录提案, @haoranba): https://github.com/agentsmd/agents.md/issues/71
- agentsfolder/spec 规范: https://github.com/agentsfolder/spec
- dotagents 标准: https://github.com/bgreenwell/dotagents
- ACS 标准: https://acs.jackby03.com/ | https://github.com/jackby03/agentic-collaboration-standard
- Oracle Open Agent Spec: https://github.com/oracle/agent-spec
- InfoQ 报道: https://www.infoq.com/news/2025/08/agents-md/
- sgryphon 的标准化总结: https://sgryphon.gamertheory.net/2025/07/agents-md-standardisation-for-agentic-coding-systems/
