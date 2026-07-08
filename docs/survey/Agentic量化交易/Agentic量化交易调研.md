# Agentic 量化交易调研（Agentic Quantitative Trading Survey）

> 本文汇总近期若干 Agentic 量化交易（Agentic Quant Trading）相关材料，提炼其核心主张、架构范式与工程实践，并对关键事实性描述附上可追溯的 URI 引用。写作遵循本仓库 survey 文档的固定模板：**背景 → 时间线 → 核心主张/结构 → 验证来源链接**。

---

## 0. 文档信息与来源清单

| 项 | 内容 |
| --- | --- |
| 主题 | Agentic Quantitative Trading（智能体驱动的量化交易） |
| 语言 | 中英混合（术语/概念保留英文原文） |
| 编写日期 | 2026-07 |

### 0.1 一手来源（可访问，已核验）

| # | 来源 | 类型 | 链接 |
| --- | --- | --- | --- |
| S1 | TauricResearch / **TradingAgents** | 开源框架（多智能体交易） | <https://github.com/TauricResearch/TradingAgents> |
| S2 | HKUDS / **Vibe-Trading** | 开源框架（个人交易智能体） | <https://github.com/HKUDS/Vibe-Trading> |
| S3 | **QUANTSKILLS**（PandaAI 发起） | 开放量化 Skill/Agent 社区 | <https://github.com/quantskills> |

### 0.2 学术与权威补充来源（联网核验，用于强化置信度）

| # | 来源 | 说明 | 链接 |
| --- | --- | --- | --- |
| R1 | TradingAgents 论文 | Xiao et al., 2024, arXiv:2412.20138 | <https://arxiv.org/abs/2412.20138> |
| R2 | LLM Agent in Financial Trading: A Survey | 金融交易 LLM Agent 综述 | <https://arxiv.org/html/2408.06361v2> |
| R3 | FinMem | 分层记忆的 LLM 交易 Agent（ICLR/相关） | <https://openreview.net/pdf/16b8e616f6321e8572cbc74e880ed505eabe5519.pdf> |
| R4 | FINCON | 带概念化口头强化的多 Agent 金融系统（NeurIPS 2024） | <https://proceedings.neurips.cc/paper_files/paper/2024/file/f7ae4fe91d96f50abc2211f09b6a7e49-Paper-Conference.pdf> |

### 0.3 中文文章一手来源（浏览器已获取正文）

以下 4 篇微信公众号文章最初被平台反爬验证（"环境异常"）拦截，普通抓取无法读取；后通过真实浏览器渲染成功获取正文，已纳入本文总结。

| # | 标题 | 公众号 / 作者 | 日期 | 对应主题 | 链接 |
| --- | --- | --- | --- | --- | --- |
| W1 | 顶级炒股神器：利用 Agent 实现自己的 AI 炒股小助手 | 算法一只狗 / leo | 2025-08-06 | TradingAgents 中文实操（DeepSeek + 火山引擎联网） | <https://mp.weixin.qq.com/s/lWF0eNOyWwQsGdrHapBqJQ> |
| W2 | Harness Engineering for Quants：让 AI Agent 在量化金融中真正可靠的完整工程指南 | 码影AI实验室 / 墨筹 | 2026-07-02 | Harness Engineering 11 原语工程范式 | <https://mp.weixin.qq.com/s/CO4HL2VdN_fJrcPksA3jBA> |
| W3 | 59 个仓库、一站式 A 股量化技能库：QuantSkills 把量化研究拆成了 AI Agent 的"乐高积木" | AIGC聊聊智晓 / aileft | 2026-07-05 | QuantSkills 技能生态拆解 | <https://mp.weixin.qq.com/s/9k83qoyQeG6Sgxi-7C7IUg> |
| W4 | Vibe-Trading：用自然语言指挥 AI 炒股的私人交易 agent | 唯一的学习之路 / Jarvis | 2026-07-05 | Vibe-Trading 五大核心功能 | <https://mp.weixin.qq.com/s/on58WTBi7DcHWoHDVu8Y3w> |

---

## 1. 背景与动机（Why Agentic Trading Now）

传统量化交易依赖人工设计因子、规则与回测流水线；而 **Agentic Trading** 的核心转变，是把大语言模型（LLM）作为具备**规划（Plan）、工具调用（Tool Use）、记忆（Memory）与自我反思（Reflection）**能力的自主体（Agent），让"自然语言意图 → 可执行策略 → 回测验证 → 风险管控"整条链路由智能体协作完成。

学术界已系统性梳理这一方向：[《Large Language Model Agent in Financial Trading: A Survey》(arXiv:2408.06361)](https://arxiv.org/html/2408.06361v2) 指出，LLM 金融交易 Agent 的能力主要沿**数据感知、记忆机制、多智能体协作、反思迭代**等维度展开，并展望了其在自动化交易中的研究方向。

驱动力可归纳为三点：

1. **认知型任务的自动化**：新闻/研报/情绪解读等非结构化信息处理，恰是 LLM 擅长的领域。
2. **多角色协作模拟**：真实交易机构由分析师、研究员、交易员、风控组成，天然适合用多 Agent 分工建模——这正是 [TradingAgents](https://github.com/TauricResearch/TradingAgents) 的设计出发点。
3. **人机交互降门槛**：从"写代码/配因子"降到"说一句话"，如 [Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) 主打的 "One Command / 自然语言生成可执行策略"。

---

## 2. 代表性项目时间线与一览

| 项目 | 主体 | 定位 | 关键范式 | 来源 |
| --- | --- | --- | --- | --- |
| TradingAgents | Tauric Research | 多智能体交易研究框架 | 交易公司角色分工 + 结构化辩论 | [GitHub](https://github.com/TauricResearch/TradingAgents) / [arXiv](https://arxiv.org/abs/2412.20138) |
| Vibe-Trading | 港大 HKUDS | 个人交易智能体 / 研究工作台 | 自然语言 → 策略 + 多数据源 + Swarm | [GitHub](https://github.com/HKUDS/Vibe-Trading) |
| QUANTSKILLS | PandaAI 发起 | 开放量化 Skill/Agent 社区 | 把量化经验封装为可检索/安装/验证的 Skill | [GitHub](https://github.com/quantskills) |
| FinMem | 学术 | 分层记忆交易 Agent | Profiling + 分层 Memory | [PDF](https://openreview.net/pdf/16b8e616f6321e8572cbc74e880ed505eabe5519.pdf) |
| FINCON | 学术 | 多 Agent 金融决策系统 | 概念化口头强化（verbal reinforcement） | [PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/f7ae4fe91d96f50abc2211f09b6a7e49-Paper-Conference.pdf) |

---

## 3. 逐项目详解

### 3.1 TradingAgents：以"交易公司"为隐喻的多智能体框架

**核心主张**：[TradingAgents](https://github.com/TauricResearch/TradingAgents) 将复杂交易任务**分解为专职角色**，模拟真实交易公司的协作动态，通过智能体间的**动态讨论（dynamic discussion）**逼近最优策略。

**角色分工（Agent Roles）**（源自 [README](https://github.com/TauricResearch/TradingAgents)）：

- **Analyst Team（分析师团队）**
  - Fundamentals Analyst：评估公司财务与基本面，识别内在价值与风险信号。
  - Sentiment Analyst：聚合新闻标题、StockTwits、Reddit 等情绪，判断短期市场情绪。
  - News Analyst：监控全球新闻与宏观指标，解读事件对市场的影响。
  - Technical Analyst：使用 MACD、RSI 等技术指标预测价格走势。
- **Researcher Team（研究员团队）**：由**看多（bullish）与看空（bearish）研究员**组成，通过**结构化辩论**权衡收益与风险。
- **Trader Agent（交易员）**：综合分析师与研究员报告，决定交易时机与规模。
- **Risk Management & Portfolio Manager（风控与组合经理）**：持续评估波动率、流动性等风险；组合经理对交易提案做最终**批准/拒绝**，通过后订单发往**模拟交易所**执行。

**工程实现要点**：

- 基于 **LangGraph** 构建，强调灵活性与模块化；支持 OpenAI、Google、Anthropic、xAI、DeepSeek、Qwen、GLM、MiniMax、Ollama 等多家 LLM Provider（见 [README - Implementation Details](https://github.com/TauricResearch/TradingAgents)）。
- **持久化与恢复（Persistence & Recovery）**：默认开启决策日志（decision log），每次运行将决策追加到 `~/.tradingagents/memory/trading_memory.md`，并在下次同标的运行时回灌"已实现收益 + 反思"，形成经验积累；可选的 **checkpoint resume** 让崩溃的运行从最后成功步骤恢复。
- **可复现性（Reproducibility）**：README 明确指出，由于 LLM 采样的非确定性与实时数据变动，**同一标的同一日期两次运行结果可能不同**，这是研究工具的预期行为而非缺陷；框架定位为"研究脚手架"，回测数字**不保证可复现**。

**学术出处**：论文 [TradingAgents: Multi-Agents LLM Financial Trading Framework (arXiv:2412.20138)](https://arxiv.org/abs/2412.20138)，作者 Yijia Xiao、Edward Sun、Di Luo、Wei Wang；[Tauric Research 项目页](https://tauric.ai/research/tradingagents/)亦提供说明。

> ⚠️ 免责声明（框架自述）：TradingAgents 面向研究用途，**不构成投资建议**，交易表现受模型、温度、周期、数据质量等多因素影响。

**中文社区实操视角（来源 W1）**：公众号"算法一只狗"的文章《顶级炒股神器：利用 Agent 实现自己的 AI 炒股小助手》给出了国内落地路径——用 **DeepSeek API 替代 GPT-4o**，并借助**火山引擎的联网能力**为 DeepSeek 补上互联网搜索（构建 R1 联网接口）；通过 `conda create -n tradingagents python=3.13` 建环境、`streamlit run app.py` 启动，输入股票代码并选择 `market/fundamentals/news/social` 分析类型。文中以 **TSLA** 为例走完"技术指标→基本面→新闻情绪→多空辩论→最终建议（结论为卖出）"全流程，并强调 AI 只是辅助、不能替代个人判断。这印证了 TradingAgents 的"多角色协同 + 快/慢思考模型动态选用"设计在国产模型栈上同样可复现。

---

### 3.2 Vibe-Trading：一句话驱动的个人交易智能体

**核心主张**：[Vibe-Trading](https://github.com/HKUDS/Vibe-Trading)（港大 HKUDS 团队）是一个开源研究工作台，把**自然语言提问**连接到市场数据加载、策略生成、回测引擎、报告导出与持久记忆，主打 "One Command to Empower Your Agent with Comprehensive Trading Capabilities"。第三方报道其已达数千 Star 量级（见 [腾讯云社区报道](https://cloud.tencent.com/developer/article/2664475) 与 [AI 工具集介绍](https://ai-bot.cn/vibe-trading/)）。

**关键能力（Key Features）**（源自 [README](https://github.com/HKUDS/Vibe-Trading)）：

1. **Self-Improving Trading Agent**：自然语言市场研究、策略草稿、文件/网页分析，带记忆的工作流。
2. **Multi-Agent Trading Teams（Swarm）**：投资、量化、加密、风控团队，流式进度 + 持久化报告；README 列出 **29 个 swarm 预设**（如 `investment_committee`：Bull/Bear 辩论 → 风控评审 → PM 定夺）。
3. **Cross-Market Data & Backtesting**：覆盖 A 股 / 港美股 / 加密 / 期货 / 外汇；**18 个市场数据源**带**按 IP 封禁风险排序的自动回退链（smart fallback）**，一个 `get_market_data` 调用即可（见 [Data Sources 章节](https://github.com/HKUDS/Vibe-Trading)）。
4. **Shadow Account（影子账户）**：解析券商流水（同花顺/东财/富途/通用 CSV）→ 行为画像（持有天数、胜率、盈亏比、处置效应、过度交易、追涨、锚定）→ **提取你的交易规则** → 回测影子策略 → 生成 HTML/PDF 报告，量化"你在实盘中漏掉了多少收益"。

**工程与架构要点**：

- **Agent Harness（2026-04-16 更新）**：跨会话持久记忆、FTS5 会话检索、可自演化的 Skills（完整 CRUD）、5 层上下文压缩、读写工具批处理。
- **Alpha Zoo**：内置 **456 个预制横截面 alpha 因子**，分 4 个 zoo——`qlib158`（Microsoft Qlib，Apache-2.0）、`alpha101`（[Kakushadze 2015, arXiv:1601.00991](https://arxiv.org/abs/1601.00991)）、`gtja191`（国泰君安 2014《191 短周期交易 Alpha 因子》）、`academic`（Fama-French 5 + Carhart 等）；带 **AST 纯度门禁 + lookahead 未来函数守卫 + pytest-socket 断网开关**。
- **Finance Skill Library**：8 大类共 **79 个金融 Skill**；**29 个 swarm 预设**。
- **连接器优先（Connector-first）券商架构**：IBKR（本地只读）、Robinhood Agentic Trading（OAuth）、Tiger/Longbridge/Alpaca/OKX/Binance/Futu/Dhan/Shoonya 等约 10 家券商，多数为 **paper + read-only**。
- **多渠道交付（IM Channels）**：同一 session runtime 可接入 16 个消息适配器（Telegram、Slack、Discord、飞书、企业微信、钉钉等）。
- **导出**：一条命令导出 TradingView（Pine Script v6）、TDX（通达信/同花顺/东财）、MetaTrader 5（MQL5）。

**安全边界（Safety Model）**——这是该项目着墨极多的部分：

- 自主交易采用**用户承诺的 mandate（标的范围/单笔规模/敞口/杠杆/日内上限）** + **文件系统级即时 kill switch（急停）** + **fail-closed 的下单前门禁（pre-trade gate）** + **完整审计台账（audit ledger）**（见 [Connector 相关 News](https://github.com/HKUDS/Vibe-Trading)）。
- 项目**不托管资金、不作为交易场所**——券商持有资金并执行，Agent 仅传递意图；用户可随时暂停。
- 一系列安全加固：API 需鉴权（`API_AUTH_KEY`）、shell 工具需显式 opt-in（`VIBE_TRADING_ENABLE_SHELL_TOOLS=1`）、CSRF/SSRF 防护、生成代码只继承 allowlist 子进程环境、Docker 以非 root 用户运行且默认仅绑定 `127.0.0.1`。

> ⚠️ Vibe-Trading 自述：自主交易能力为 **Experimental / use at your own risk**，且不在用户设定的限额外交易。

**中文解读视角（来源 W4）**：公众号"唯一的学习之路"（作者 Jarvis）的《Vibe-Trading：用自然语言指挥 AI 炒股的私人交易 agent》提炼了五大价值点：① 自然语言驱动（如"帮我找最近 3 个月表现最好的动量因子"）；② **影子账户**可连真实券商账户（如 Trading 212），实盘前先跑模拟并过前置风控；③ **16 个消息渠道**（Telegram/飞书/企业微信/钉钉等）直接聊天下指令；④ **因子加速引擎**（NumPy/Bottleneck 快路径 + 并行基准测试）；⑤ **MCP + Ollama 本地模型**实现数据与模型完全私有化。文章结论强调：其最大价值不在"赚钱"，而在把量化完整流程（因子研究→回测→风控→执行）用 Agent 方式重做一遍，是量化入门的绝佳学习案例。

---

### 3.3 QUANTSKILLS：把量化经验封装为"人类可信、Agent 可调用"的 Skill

**核心主张**：[QUANTSKILLS](https://github.com/quantskills)（由 PandaAI 发起）是"AI Agent 时代的开放量化社区"，聚焦两类资产——**Quant Skills（量化技能）** 与 **Agents（智能体）**，目标是把交易经验、研究方法、因子模型与策略代码，转化为**可检索、可安装、可验证、可分享**的标准化资产。官网见 <https://quantskills.ai>。

**收录内容与组织方式**（源自 [组织 README](https://github.com/quantskills)）：

- **Skills（`skill-` 前缀）**：可复用能力，如因子计算、数据清洗、策略审计、研报复现、报告生成。社区已列出数十个 Skill 仓库，例如：
  - `skill-quant-factor-directional-alpha`：**296 个**方向类 OHLCV 因子 Skill，真实行情验证 296/296 通过。
  - `skill-quant-factor-risk-pattern-alpha`：**288 个**风险状态/形态类因子。
  - `skill-quant-factor-volume-stat-alpha`：**216 个**量能/量价/统计类因子。
  - `skill-backtest`：截面多头回测**标准协议**——T+1 开盘成交、Top 等权、双边 15bp、涨跌停剔除、四联诊断图、5 项健康度自检。
  - `skill-factormad-debate-factor-mining`：**FactorMAD** 多智能体**辩论式**因子挖掘。
  - `skill-paper-replication` / `skill-report-replication`：把论文/研报变成可运行、可审计的复现实验（检索→提取→回测→图表→指标对照）。
- **Agents（`agent-` 前缀）**：研究复现、策略审计、市场状态监控等工作流，如 `agent-market-regime-monitor`、`agent-crowding-risk-monitor`、`agent-quantspace`。

**治理与验证等级（Validation Levels）**——这是 QUANTSKILLS 区别于普通仓库集合的关键机制：

| 等级 | 要求 | 适用对象 |
| --- | --- | --- |
| 📋 Level 1 · Listed | 基本信息清晰、可进入目录 | 研究方法、Prompt 型 Skill、早期想法 |
| ▶️ Level 2 · Runnable | 安装说明 + 示例输入输出 + 可运行代码 + 依赖 | 因子计算、数据处理、报告生成 |
| ✅ Level 3 · Verified | 数据来源 + **无未来函数检查** + 回测证据 + 风险说明 + 验证报告 | 可交易策略、因子/策略研究 |

- 声明文件约定：Skill 仓库放 `SKILL.md`，Agent 仓库放 `AGENTS.md`，并携带上游元数据（组织 URL、仓库名、类型等）。
- 面向 **AI Agent 的发现机制**：规划中的 `llms.txt`、Skills/Agents 索引、**MCP 服务**、GitHub Topics/Release 约定，让 Agent 能"搜索→安装→调用→验证"社区量化能力。
- 社区规则强调：量化项目**必须明确数据来源、假设、局限与风险边界**，成员仓库默认 Community Project，未经评审不得宣称"官方/已验证"。

> 💡 一句话定位：QUANTSKILLS 补的是 **Agent 生态的"能力供给侧"**——不造一个交易 Agent，而是把可信、可验证的量化能力做成 Agent 可调用的标准件。

**中文解读视角（来源 W3）**：公众号"AIGC聊聊智晓"（作者 aileft）的《59 个仓库……乐高积木》补充了若干关键事实与细节：QuantSkills 组织**创建于 2026-06-02**，当时已发布 **59 个公开仓库**、约 81 关注者，专注 A 股，数据基座为 **Pandadata**。文中深度拆解了五个代表性技能：① **Smart Money Profiler**（席位画像/北向跨期/资金合力三支柱，采用"反撞车设计"避免功能重叠）；② **Backtest**（不是框架而是"协议"：T+1 开盘入场、等权、涨跌停剔除、双边 15bp、五项健康度自检）；③ **Factor Debug**（9 类症状速查表 + 6 类经典未来函数模式）；④ **Portfolio Checkup**（8 章体检，核心是按权重聚合风险敞口）；⑤ **Stock Screener**（自然语言语义→ 13 种标准过滤器、七层筛选漏斗、杜绝未来函数）。技能包经由 `SKILL.md` + `references/` + `agents/` 多平台适配（Claude Code / Cursor / Codex / OpenClaw）。文章也坦言局限：仅依赖 Pandadata、仅覆盖 A 股、社区规模尚小、非实盘就绪、技能质量参差。

---

### 3.4 学术脉络补充：记忆与多智能体强化

为强化置信度，补充两篇有代表性的学术工作，它们与上述工程项目在设计上高度呼应：

- **FinMem**：提出带 **Profiling（画像）+ 分层记忆（Layered Memory）** 的 LLM 交易 Agent，用于处理多源金融数据并增强交易表现——与 Vibe-Trading 的"持久记忆 / 交易画像"和 TradingAgents 的"决策日志回灌"思路一致（[PDF](https://openreview.net/pdf/16b8e616f6321e8572cbc74e880ed505eabe5519.pdf)）。
- **FINCON**：一个带**概念化口头强化（conceptual verbal reinforcement）**的合成式 LLM 多 Agent 系统，面向单股交易与组合管理等关键金融任务——与 TradingAgents 的"结构化辩论/风控评审"范式同源（[NeurIPS 2024 PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/f7ae4fe91d96f50abc2211f09b6a7e49-Paper-Conference.pdf)）。

综述 [arXiv:2408.06361](https://arxiv.org/html/2408.06361v2) 则把这些工作统一在"数据 / 记忆 / 多智能体 / 反思"的分析框架下。

---

### 3.5 Harness Engineering for Quants：让量化 Agent 真正可靠的工程范式（重点）

> 来源：W2 —《Harness Engineering for Quants：让 AI Agent 在量化金融中真正可靠的完整工程指南》（公众号"码影AI实验室"，墨筹，2026-07-02）。这篇文章不介绍某个具体项目，而是提出**方法论层面的框架**，与本仓库 `quant-agent` 采纳的设计哲学高度一致，故单独成节详述。

**核心命题**：`Agent = 模型 + Harness`。模型提供原始智能，Harness 是除此之外的一切——**可靠性恰恰是在 Harness 中被构建或被摧毁的**。文章援引 HashiCorp 联合创始人 Mitchell Hashimoto 2026-02-05 的定义："每当发现 Agent 犯了一个错误，你就花时间去工程化一个解决方案，确保这个错误永远不会再发生。"随后 OpenAI 发布《Harness Engineering: Leveraging Codex in an Agent-First World》使该词成为核心概念。

**关键证据**：LangChain 的编码 Agent 在 **Terminal Bench 2.0** 上从 Top 30 之外跃升到 Top 5，提升 **13.7 个百分点（52.8% → 66.5%）**，**全程未更换底层模型**（固定 GPT-5.2-Codex），只改了系统提示词、工具与中间件钩子——即"智能没变，智能周围的环境全变了"。

**工程演进定位**：

- Prompt Engineering（2023–2024）：优化单次交互指令。
- Context Engineering（2025 中期）：管理系统级上下文（RAG / MCP / 记忆）。
- **Harness Engineering（2026）：为 Agent 设计完整的运行环境**——面向持续数小时、跨多 Agent、大部分无人参与的量化研究流程。

**生产级 Harness 的 11 个原语（11 Primitives）**：

| # | 原语 | 量化场景要点 |
| --- | --- | --- |
| 1 | 指令层（Instruction） | AGENTS.md 当"目录"（约 100 行）指向 `docs/`；编码结构性约束：复权收盘价、禁用目标衍生特征、回测须含熊市周期、因子假设先记录再写代码 |
| 2 | 上下文交付（Context Delivery） | 把订单簿、收益序列、既有因子库、基准规范递到模型手上，而非凭记忆 |
| 3 | 上下文管理（Context Mgmt） | 谁决定此刻什么上下文重要：RAG 检索、重排序、会话摘要、压缩 |
| 4 | 工具接口（Tool Interface） | 以 MCP 暴露行情/回测/因子库/风险模型/组合优化/执行/版本控制；原则是**幂等 + 有界范围**，下单工具须人类审批门禁 |
| 5 | 执行环境（Execution Env） | 用工程约束让 Agent **结构性地不可能**碰生产密钥/实盘持仓；每次研究会话在干净、固定数据与库版本下运行 |
| 6 | 持久状态（Persistent State） | 记住尝试过什么、为何失败——迭代的引擎。引用微软 **RD-Agent(Q)**（NeurIPS 2025）：年化约为 Alpha158/Alpha360 的 **2 倍**、因子数减少 **70%+**、每次优化成本 **<10 美元** |
| 7 | 编排（Orchestration） | 假设→因子代码→单测→**清除交叉验证**回测→基准对比→记录→夏普达标则开 PR，否则带失败原因回到假设生成；不得跳步 |
| 8 | 子 Agent（Sub-agents） | Anthropic 的 Planner/Generator/Evaluator 三 Agent 结构能自动捕获单 Agent 漏掉的"技术可用但底层有问题"的失败 |
| 9 | 技能与程序（Skills） | 可复用的"已命名程序"，消除"每次重造方法并引入微妙错误"；回测技能每次用相同封锁期/前向窗口/成本模型，不许即兴发挥 |
| 10 | 验证与可观测性（Verify/Observe） | "我完成了"不是证据，**Harness 需要收据**：无数据错误、样本外 IC、夏普高于底线、回撤达标、通过前视偏差检测 |
| 11 | Harness 演化（Evolution） | 每次犯错就在 Harness 里工程化永久修复，使该错误结构上不可能重演；"技术债像高息贷款，持续小额偿还" |

**六大失败模式 → Harness 修复**（量化专属）：

| 失败模式 | Harness 修复层 |
| --- | --- |
| 因子构建前视偏差 | 执行环境强制数据 API 要求 `as_of_date` 参数 |
| 长会话上下文溢出 | 持久状态层在会话开始时重新检查原始假设 |
| 用微妙错误重造方法 | 固化为已命名技能，Agent 不重新实现 |
| 静默工具失败 | 工具接口在返回前校验响应完整性 |
| 子 Agent 不一致 | 指令层 + 技能层统一编码数据标准 |
| 未经验证的完成 | 编排层验证门禁：回测通过才能开 PR |

**8 周落地路线图**：第 1–2 周建 `QUANT_AGENTS.md` + 数据标准 + 沙箱回测环境；第 3–4 周用 MCP 定义行情/因子/回测/IC 工具；第 5 周建假设日志与回测结果日志并接编排；第 6 周固化清除交叉验证、IC 计算、前视偏差检测等技能；第 7 周加验证门禁与循环检测中间件 + 全链路追踪；第 8 周起每周做 Harness 审查。

**方法论转变**：当 Agent 产出错误结果时，本能是"怪模型"，正确姿势是问"**Harness 的哪一层没能阻止这个错误**"。对量化而言，一个错误因子消耗真金白银、系统性错误会在数百个策略上复利——这是"研究操作可规模化"与"悄悄失败"的区别。

> 🔗 与前述项目的呼应：TradingAgents 的决策日志（原语 6）、Vibe-Trading 的 mandate/kill switch/审计台账（原语 4/5/10）、QUANTSKILLS 的无未来函数验证与标准回测协议（原语 9/10），都可视为 11 原语在具体系统中的实例化。

---

## 4. 横向对比（Architecture Paradigms）

| 维度 | TradingAgents | Vibe-Trading | QUANTSKILLS |
| --- | --- | --- | --- |
| 定位 | 多智能体交易**研究框架** | 个人交易智能体 / **研究工作台** | 量化能力的**开放社区/注册表** |
| 核心隐喻 | 模拟交易公司角色分工 | 一句话 → 策略 + Swarm 团队 | Skill/Agent 作为可验证资产 |
| 协作方式 | 看多/看空**结构化辩论** + 风控终审 | 29 个 Swarm 预设（含投委会辩论） | FactorMAD 辩论式因子挖掘等 |
| 记忆机制 | 决策日志 + 反思回灌 | 跨会话持久记忆 + FTS5 检索 | （由各 Skill/Agent 自定） |
| 数据/回测 | 依 Yahoo 等，多市场 | **18 数据源自动回退** + 多引擎回测 | 标准回测协议 + 真实行情验证 |
| 落地形态 | LangGraph + CLI/Python | CLI/Web/MCP + 16 IM 渠道 | GitHub 仓库 + 计划中的 MCP |
| 实盘/安全 | 模拟交易所 + 免责声明 | mandate + kill switch + 审计台账 | 强制声明数据源/假设/风险边界 |
| 可复现性态度 | 明确"不保证复现" | 未来函数守卫 + 校验产物 | Verified 等级要求无未来函数 |

**共性设计模式（Cross-cutting Patterns）**：

1. **角色分解 + 辩论/评审**：用多 Agent 分工替代单体，用 Bull/Bear 辩论与风控终审对抗单点偏差。
2. **记忆与反思**：决策日志、跨会话记忆、经验回灌，使 Agent 具备"越用越好"的潜力。
3. **工具优先（Tool-first）与数据接地（Grounding）**：强调让 Agent 通过真实数据/工具作答，而非"凭训练记忆编造"（Vibe-Trading README 明确点名这一风险）。
4. **可验证与防作弊**：无未来函数（look-ahead）检查、AST 纯度门禁、断网测试、随机对照——直击量化回测的"过拟合/未来函数"痼疾。
5. **安全边界前置**：mandate/kill switch/审计台账/只读默认，把"自主交易"关进可控的笼子。

---

## 5. 风险与局限（Risks & Caveats）

- **非确定性**：LLM 采样导致结果不可字节级复现，回测数字不可作为策略承诺（TradingAgents 明示）。
- **数据时效与未来函数**：实时新闻/情绪随时间变化；未来函数（look-ahead bias）是首要工程风险，多个项目都为此设专门守卫。
- **不构成投资建议**：三个项目均以研究/教育定位，自主实盘为实验性能力，需用户自担风险。
- **过拟合与选择偏差**：QUANTSKILLS 甚至专设 `skill-backtest-overfit` 检测多重检验带来的过拟合。

---

## 6. 对 JanusAgent / quant-agent 的启示

结合本仓库 `quant-agent` 采用的 Harness Engineering 设计哲学，这些外部实践可直接映射：

1. **角色与辩论范式**：quant-agent 的策略引擎可借鉴 TradingAgents 的"分析→看多/看空辩论→交易→风控终审"分层，把用户"涨卖跌买 / 适当追涨"的策略拆到不同 Agent 职责中形式化。
2. **记忆回灌**：仿照 TradingAgents 的决策日志 + 反思，把每次回测/实盘结果沉淀为可回灌的经验，服务"越用越准"。
3. **Skill 化与可验证**：借鉴 QUANTSKILLS 的 `SKILL.md`/`AGENTS.md` + 三级验证（Listed/Runnable/Verified），把因子、选股、仓位规则封装为**带无未来函数检查**的可验证 Skill。
4. **安全护栏**：引入 Vibe-Trading 式的 mandate + kill switch + 审计台账，作为任何"自主下单"能力的前置约束。
5. **数据接地与工具优先**：所有事实性市场判断必须来自工具/数据源，禁止 LLM 凭记忆编造——这与本仓库"事实与推断分离"的文档规范一致。

---

## 7. 验证来源链接（References）

**一手开源项目**

- TradingAgents（GitHub）：<https://github.com/TauricResearch/TradingAgents>
- Vibe-Trading（GitHub）：<https://github.com/HKUDS/Vibe-Trading>
- Vibe-Trading 中文 README：<https://github.com/HKUDS/Vibe-Trading/blob/main/README_zh.md>
- QUANTSKILLS（GitHub 组织）：<https://github.com/quantskills>
- QUANTSKILLS 官网：<https://quantskills.ai>

**学术与论文**

- TradingAgents 论文（arXiv:2412.20138）：<https://arxiv.org/abs/2412.20138>
- Tauric Research 项目页：<https://tauric.ai/research/tradingagents/>
- LLM Agent in Financial Trading: A Survey（arXiv:2408.06361）：<https://arxiv.org/html/2408.06361v2>
- FinMem（OpenReview PDF）：<https://openreview.net/pdf/16b8e616f6321e8572cbc74e880ed505eabe5519.pdf>
- FINCON（NeurIPS 2024 PDF）：<https://proceedings.neurips.cc/paper_files/paper/2024/file/f7ae4fe91d96f50abc2211f09b6a7e49-Paper-Conference.pdf>
- Kakushadze, 101 Formulaic Alphas（arXiv:1601.00991）：<https://arxiv.org/abs/1601.00991>

**第三方报道**

- 腾讯云社区：港大开源 AI 量化神器 Vibe-Trading：<https://cloud.tencent.com/developer/article/2664475>
- AI 工具集：Vibe-Trading 介绍：<https://ai-bot.cn/vibe-trading/>

**中文文章（微信公众号，浏览器已获取正文）**

- W1《顶级炒股神器：利用 Agent 实现自己的 AI 炒股小助手》（算法一只狗）：<https://mp.weixin.qq.com/s/lWF0eNOyWwQsGdrHapBqJQ>
- W2《Harness Engineering for Quants》（码影AI实验室）：<https://mp.weixin.qq.com/s/CO4HL2VdN_fJrcPksA3jBA>
- W3《59 个仓库、一站式 A 股量化技能库：QuantSkills》（AIGC聊聊智晓）：<https://mp.weixin.qq.com/s/9k83qoyQeG6Sgxi-7C7IUg>
- W4《Vibe-Trading：用自然语言指挥 AI 炒股的私人交易 agent》（唯一的学习之路）：<https://mp.weixin.qq.com/s/on58WTBi7DcHWoHDVu8Y3w>

---

> 说明：本文所有事实性描述均标注了对应 URI。三个 GitHub 项目内容基于官方 README 抓取核验；学术与报道类链接经联网检索确认；4 篇微信公众号文章最初被平台反爬拦截，后通过真实浏览器渲染成功获取正文并已合并进第 3 章（其中 W2 独立成 3.5 节，W1/W3/W4 分别并入 3.1/3.3/3.2）。
