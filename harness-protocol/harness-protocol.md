# Harness + Loop 执行协议

> 创建日期：2026-06-30
> 作者：晨珺 + Sisyphus
> 用途：定义「我（决策）+ OMO（harness）+ codemaker（loop body）」三方协作的执行纪律
> 实证依据：`docs/ovrt-doc-audit/experiment-log.md`（57 Turns，4 轮冻结门，10 P0 捕获）
> 关联：`docs/playwright-cdp-verification.md`（验收工具）

---

## 一、三方分工

| 角色 | 定位 | 职责 | 决策带宽占用 |
|---|---|---|---|
| **晨珺** | 唯一决策者 | 目标定义 + 优先级裁决 + P0 修还是接受 + 验收拍板 + review diff | 高（只花在判断上） |
| **OMO (Sisyphus)** | harness 外脑 | Plan 草案 + Freeze 双审 + Verify 全量 + Log 自动化 | 不占晨珺带宽 |
| **codemaker** | loop body 执行手 | Execute 阶段代码实现 + 验收脚本编写 | 低（晨珺只 review diff） |

**核心原则**：晨珺的决策带宽只花在「做判断」上，不花在「收集信息」和「执行操作」上。OMO 让晨珺看到全貌且不遗漏，codemaker 让晨珺不用亲手写每一行代码。

---

## 二、Harness 五阶段（全量，不可裁剪）

### 2.1 Plan

- **执行者**：OMO（explore 并行搜索）+ 晨珺（裁决）
- **产出**：草案（方案 + 影响文件 + 验收标准）
- **强制项**：草案必须标注「触发条件在开发环境能否复现？」——不能复现 → 草案必须包含模拟方案
- **并行优化**：explore 搜索与「读 experiment-log 末尾确定 Turn 编号」无依赖，同时启动
- **晨珺动作**：审阅草案，裁决方向（如 Turn 8-9 的 M1/M2/M3 对齐）

### 2.1.5 前端验收门禁（涉及前端时触发）

> **触发条件**：Plan 草案涉及前端 UI 改动（新增组件 / 改交互逻辑 / 改视觉布局）时，**必须**在 Freeze 之前先走前端验收。纯后端 / 纯文档 / 纯配置改动不触发。
>
> **⚠️ 交互稿制作协议**：制作验收稿前**必须**先阅读 [`preview-prototype-protocol.md`](preview-prototype-protocol.md)——该文档定义了"完全按照生产环境复刻"的 6 步流程 + 4 类常见陷阱（data-theme 错位 / CSS 类冲突 / 颜色多源 / 缺框架）+ 验证清单。跳过该文档会导致交互稿与生产环境视觉不一致（case-rollout module-1 实证：4 轮修正才达到一致）。

- **执行者**：OMO（制作验收稿）+ 晨珺（验收拍板）
- **产出**：单文件 HTML 验收稿（参考 `splash-preview.html` / `ue4-connect-preview.html` 形式）
- **验收稿必须包含**：
  1. **场景切换器**（顶部）：覆盖所有 UI 状态（如已连接 / 未连接 / 检测中 / 错误），一键切换
  2. **预览控制条**（右下）：模拟操作按钮（如"模拟连接成功""模拟断开"），实时状态标签
  3. **V7 Token 合规自证**：复用 V7 Token（`--v7-bg-carbon` / `--v7-accent` / `--v7-warning` 等），不硬编码颜色。验收稿头部必须嵌入 Stylelint 零违规自证（见 §2.1.5.1）
  4. **固定视口布局**：`height: calc(100vh - Npx)` + 内部滚动，工具栏 / 操作区始终可见，不顶出屏幕
  5. **可交互**：按钮可点击触发状态变化，popover 可开关，Toast 可弹出——不是静态截图
  6. **生产级 CSS 保真**（GP-11 实证 + Google UI review 标杆）：验收稿**必须引用生产 CSS 文件**（`ui-shell/css/` 下的实际样式表），而非手写简化版 CSS。HTML DOM 结构必须与目标组件的真实 DOM 结构一致——不做结构简化。**禁止"简化版"验收稿**（GP-11 教训：简化 mockup 按钮被裁剪，生产环境不复现 → 验收无意义）。行业对标：Google eng-practices "UI 变更必须提供可交互演示" + UXPin 高保真原型定义"使用真实 UI 组件、实际内容、交互逻辑"
- **晨珺动作**：浏览器打开验收稿，逐场景验证交互逻辑是否符合预期。**通过 → 进 Freeze；不通过 → 回 Plan 修订**
- **纪律**：前端验收未通过 = 不得进入 Freeze / Execute。即使用户说"先实现再说"，也必须先出验收稿确认交互逻辑——代码实现基于验收稿，避免实现完才发现交互方向错误
- **实证依据**：UE4 连通引导任务（2026-06-30）——先出设计文档 → 用户要求"直接给我看 HTML 验收" → 出 `ue4-connect-preview.html` → 用户发现布局顶出屏幕 → 修复后才确认交互逻辑。证明文字设计稿不足以验证前端交互，必须可交互验收

### 2.1.5.1 V7 Design Token 自动化合规门禁（Stylelint）

> **行业对标**：Google eng-practices "On matters of style, the style guide is the absolute authority"。业界通过自动化工具（Stylelint）而非人工审查强制样式规范。**不是"建议对齐"，而是"CI 阻断"**。
> **实证**：GP-5 单屏 13 个 V2 合规违规均因无自动化合规检查

- **工具**：Stylelint（框架无关 CSS linter，无需 Storybook/React）
- **配置**（项目根目录 `.stylelintrc.js`）：禁止 hex/rgb/hsl 硬编码颜色，强制 `--v7-*` Token 命名，颜色类属性必须使用 `var()` 引用 Token
- **CI 集成**：`npx stylelint "ui-shell/**/*.css"`。任何硬编码颜色 → CI 失败 → 阻断合并
- **落地时机**：纪律条款生效即需安装（`npm create stylelint@latest` + 复制配置）。GP-5 发现的 13 个 V2 违规将在 CI 阶段被拦截
- **Momus 第 8 维度**（新增）：**设计系统合规性**——CSS 是否通过 Stylelint 零违规？Token 命名是否遵循 `--v7-*` 规范？

### 2.2 Freeze（Oracle + Momus 并行双审）

- **执行者**：OMO（Oracle + Momus 同时发射）
- **审计三轴**（对齐 experiment-log §1.2）：

| 轴 | 审计内容 | 执行者 |
|---|---|---|
| 决策审计 | 合理优雅 / 过度设计 / 有缺漏 / 该这么做 / 方向正确性 | Oracle |
| 完整性审计 | 覆盖所有受影响项 / 验收标准可观测 / 环境对等性 / 回归风险 / 文档同步 | Momus |
| 架构审计 | 是否符合现有架构 / 类型安全 / 跨模块影响 | Oracle |

- **Momus 完整性审计 7 维度**：
  1. 受影响项覆盖
  2. 验收标准可观测（必须指向具体日志行 / API 字段 / DOM 元素，**不接受「正常回复」这种模糊词**）
  3. **环境对等性**：验收项是否覆盖降级/边界路径？开发环境无法复现时是否有模拟方案？
  4. 回归风险
  5. 跨模块影响（与 Oracle 架构审计交叉覆盖）
  6. 文档同步
  7. **运行时环境交互**（GP-14 Turn 99 新增）：新引入代码与运行时环境的交互边界是否被审计——Defender 实时扫描 / 文件锁语义（ENOENT vs EBUSY vs EPERM）/ 进程启动时序（Start-Sleep 不可靠）/ 权限边界（UAC / 管理员 vs 用户）/ 网络超时 / 磁盘 I/O 争用。**与维度 3/5 互补**：维度 3 关注降级/边界验收覆盖，维度 5 关注跨模块逻辑影响，本维度关注代码与运行时环境的交互边界。**实证**：GP-14 R3 Oracle 新发现 2 P1（Start-Sleep 2s 不可靠 + openSync ENOENT vs EBUSY）均属运行时环境交互边界，R1/R2 审计未覆盖此维度

- **冻结标准**（对齐 experiment-log §1.3，2026-07-02 修订）：

| 风险等级 | 定义 | 冻结门要求 |
|---|---|---|
| P0 阻塞 | 破坏功能/安全/架构违规 | **> 0 → MUST continue** |
| P1 需修 | 边界 case/错误处理缺失 | **> 0 → MUST continue** |
| P2 可接受 | 命名/注释/微优化 | 不限，写入 log |

**冻结条件**（消除歧义）：
```
P0 == 0 AND P1 == 0  → CAN freeze（所有审计关注点已解决）
P0 > 0 OR P1 > 0     → MUST continue to next round
```

> **2026-07-02 修订说明**：废除原"P1 ≤ 2 且有 mitigation 可冻结"规则。行业对标：Google eng-practices "approve when improves code health" + GitHub Approve/Request changes 二元模型——不存在"允许 2 个未解决问题"的中间态。P1 mitigation 仍需可验证应对方案，但不再作为"解锁冻结"的豁免条款。本修订前瞻性约束，不追溯既有 Turn。P1 不收敛专项分析保留为方法论改进机制。

- **P1 mitigation 质量标准**（GP-14 Turn 99 新增）：P1 的 mitigation 必须是“可验证的应对方案”，而非“记录为 backlog”。合格 mitigation 示例：“Defender 误触发时 retry 3 次 + WARNING 日志”（可验证：模拟 Defender 隔离 → 验证 retry 生效）。不合格 mitigation 示例：“记录为 backlog，alpha-2 考虑”（不可验证，无明确触发条件）。mitigation 需标注：①触发条件 ②应对动作 ③验证方式。Verify 阶段若发现 mitigation 不可验证，升级为 P0 重新提交修正方案。**实证**：GP-14 R3 的 2 个 P1 mitigation（Start-Sleep 2s → .started_ok sentinel / openSync ENOENT vs EBUSY）均为可验证应对方案，符合本标准

- **不通过**：修复 → 重新提交，最大 3 轮；第 3 轮仍 P0 → 升级晨珺决策
- **修正者自审**（GP-14 Turn 99 新增）：每轮修正提交重新审计前，修正者（主 Agent）必须对新引入的代码做“边界 case 自查”——列出新代码与运行时环境的所有交互点（Defender 扫描 / 文件锁语义 / 进程启动时序 / 权限边界 / 网络超时 / 磁盘 I/O 争用），并标注每个交互点的预期行为与失败模式。自审结果随修正方案一同提交审计。Oracle/Momus 将自审清单作为审计起点（不是接受清单），重点核查自审未覆盖的边界，避免自审偏见导致漏判。**实证**：GP-14 Turn 95 三轮冻结门，R2 Metis 新发现 P0（PS1 重启顺序）+ R3 Oracle 新发现 2 P1（Start-Sleep 2s / openSync ENOENT vs EBUSY）均在“修正引入的新代码”中发现——若修正者在 R1→R2 修正时做边界 case 自审，R2 的 P0 和 R3 的 P1 可提前发现，预计将三轮降为两轮（**待验证假设**，后续 GP 案例中跟踪）
- **并行优化（有约束）**：R1 发现多个 P0 时，仅当修复不同文件且无逻辑依赖才并行修复后统一提交 R2；不确定是否有依赖则串行逐个修。GP-2 R1→R2 纠正教训：修正后的结论仍可能包含未验证的推断，并行修复会放大错误
- **纪律**：单轮冻结门不轻信，修正后重新审计（Turn 45 教训：R1 修正后仍可能引入新误判）
- **P1 收敛趋势监控**（GP-14 Turn 99 新增）：多轮冻结门中，如果 P1 数量不收敛（如 R1→R2→R3 为 2→2→2 或 4→2→2），由 Momus 在 Freeze R3 提交审计时触发专项分析“为什么 P1 不收敛”——检查是否为“修正引入新代码 → 新 P1”的递归模式（GP-14 Turn 95 实证），结果以 experiment-log 方法论观察格式记录。**注意**：P1 不收敛不阻塞冻结（P1≤2 有 mitigation 即可冻结），但必须记录递归模式供方法论改进。**实证**：GP-14 R1(4)→R2(2)→R3(2) 振荡，R3 仍 GO（P1=2 有 mitigation），但复盘识别出“修正引入新 P1”的结构性根因，促成本 4 项改进
- **审计模型轮换**（experiment-log §4.4 改进 1）：多轮冻结门时，R2 换 agent 类型——Metis（意图/歧义）+ Explore（事实核查）或 ultrabrain category，提供正交视角，避免同一模型共享盲区

### 2.2.1 问题解决前的行业对标强制（BADR 四步法）

> **行业对标**：Google SRE postmortem culture "事后分析不是惩罚，是学习机会" + Atlassian Sprint Retrospective 5 步模型
> **适用场景**：Freeze 阶段 Oracle/Momus 发现新类型 P0/P1（非已有模式），或 Harness 迭代中遇到方法论空白，在制定解决方案**之前**必须先做行业对标

**四步流程**（B-A-D-R）：

| 步骤 | 名称 | 操作 | 执行者 |
|---|---|---|---|
| **B**enchmark | 搜索行业实践 | 搜索 1-2 个行业来源（Google eng-practices / SRE book / Atlassian playbook / OSS 官方文档），锁定具体实践名称和来源链接 | OMO librarian 并行搜索 |
| **A**dapt | 适配团队约束 | 写 ≤3 条适配要点：对 3 人团队 / 无设计师 / Electron + vanilla CSS/JS 的适用性分析。移除需专职角色或重型工具链的实践 | OMO + 晨珺裁决 |
| **D**ecide | 选择采纳级别 | FULL（完整落地）/ SIMPLIFIED（降级适配）/ SKIP（不适用）+ 原因。晨珺最终拍板 | 晨珺 |
| **R**ecord | 记录防重 | 将结论记录到 `docs/benchmarks/` 目录（按问题域命名），避免 6 个月后重复调研 | OMO（Log subagent） |

**纪律**：
- Freeze 阶段发现新类型 P0/P1 时，Plan 修订草案**必须**附 BADR 分析。无 BADR = Momus 退回审计
- BADR 分析不阻塞 Freeze 冻结（调研在 Plan 修订时完成），但冻结后的修正方案**必须**包含行业对标依据
- `docs/benchmarks/` 目录为永久知识库，每季度由 Momus 审计是否有过时条目
- **实证**：当前协议优化的 7 个问题即为 BADR 首批产出。若 BADR 在 GP-5（13 个 V2 违规）或 GP-11（简化 mockup）发生时已存在，解决方案将在 Freeze 阶段就引入 Stylelint + 1:1 保真度规则，不依赖事后复盘

### 2.3 Execute

- **执行者**：codemaker（低上下文依赖）或晨珺（高上下文依赖）
- **分工规则**：

| 场景 | codemaker | 晨珺 |
|---|---|---|
| 单文件 <20 行逻辑修复 | ✅ | — |
| 验收脚本（CDP/curl/PowerShell 模拟） | ✅ | — |
| 文档更新（experiment-log/verification） | ✅ | — |
| 多文件联动修复 | ❌ | ✅ |
| 部署链路文件（installer.nsh / launcher.py / main.js） | ❌ | ✅（必走冻结门） |

- **并行优化（有约束）**：Execute 开始前先识别可并行的子任务（按 DAG 拆分）。**同文件多方编辑必须串行**（experiment-log §4.4 改进 4：telemetry.py 串行约束）；跨文件且无逻辑依赖可 fan-out 并行；不确定是否有依赖则串行
- **纪律**：执行中发现需偏离冻结结论 → 停，回 Freeze
- **任务时长监控**（experiment-log §4.4 改进 2）：subagent 返回后记录时长，异常长于同类任务正常范围（如 quick 任务 >5min）需人工检查产出质量

### 2.4 Verify（全量）

- **执行者**：OMO
- **必做项**：
  1. 语法检查（py_compile / makensis / node -c）
  2. CDP Playwright（涉及前端/Electron）
  3. API curl（涉及后端）
  4. **环境对等性验证**：Freeze 判定需模拟时，必须构造模拟场景并跑验收
- **并行优化（有约束）**：前 3 项（语法检查 / CDP Playwright / API curl）无依赖，先启动环境后并行执行；**环境对等性验证必须最后跑**——它可能破坏运行环境（如重命名 vendor/openclaw-runtime/、清空 code_version.txt），若先跑会导致前 3 项结果不可信
- **模拟场景示例**（基于 GP bug 实证）：

| GP bug 类型 | 模拟方式 |
|---|---|
| 降级路径（GP-1） | 重命名 `vendor/openclaw-runtime/` → 启动 → 切模型 → 查 server.log |
| 首次安装（GP-2） | 清空 `code_version.txt` + 重命名 pip → 启动计时 |
| 安装路径（GP-3） | 干净虚拟机双击 Setup.exe |

- **晨珺动作**：审阅结果，拍板「通过 / 打回」

### 2.4.1 打包验收路径矩阵（Turn 41/87/98 实证 + VS Code Sanity Check 标杆）

> **触发条件**：改动涉及 Electron main.js / installer.nsh / launcher.py / resources/backend/ / 任何 vendor_* 目录时，必须按本矩阵选择验收路径。纯后端（src/api, src/services, src/db）/ 纯前端（ui-shell/）改动不触发本矩阵。

| 改动类型 | deploy_local | 打包.bat | asar extract 验证 | CDP 验证 | 多路径验收 |
|---|---|---|---|---|---|
| 纯后端 | ✅ | — | — | — | — |
| 纯前端 | ✅ | — | — | ✅ | — |
| Electron main.js | — | ✅ 必须 | ✅ 必须 | ✅ 必须 | 视改动 |
| installer.nsh | — | ✅ 必须 | — | — | — |
| launcher.py | ✅（手动复制） | — | — | — | — |
| resources/backend/ | 手动 Copy+SHA256 | — | — | — | — |

**关键约束**：
- **asar 手动重打包不可靠**（Turn 41 实证）。唯一可靠方式是打包.bat 全量打包。禁止用手动 asar 重打包作为验收方式
- **deploy_local 不覆盖 Electron main.js**（Turn 87 实证）。改 main.js 必须走打包.bat
- **sync_from_dev 排除 resources/backend/**（Turn 97 实证）：需手动 Copy-Item + SHA256
- **schtasks 残留清理**（Turn 101/102 实证）：Verify 前后必须清理 schtasks 残留任务 + marker 文件，否则验收环境污染下一轮结果

### 2.4.2 多路径验收标准化（Turn 98 GP-17 实证 + VS Code regression card 标杆）

> **触发条件**：改动涉及"自动清理 / 自动修复 / 降级路径 / 故障自愈 / marker 文件"时，必须按本标准执行多路径验收。

| 验收路径 | 初始状态 | 验证目标 | 实证 |
|---|---|---|---|
| normal | 无 marker / 无障碍 | 正常启动流程完整 | 所有 GP |
| restart_failed | `.restart_failed` marker 存在 | 恢复路径触发 + sentinel 重写 | GP-17 |
| cleanup_failed | `.cleanup_failed` marker 存在 | killAndCleanVendor + schtasks fallback | GP-14 |
| 首次安装 | 清空 code_version.txt | 首次安装计时 + vendor 解压 | GP-2 |
| 降级路径 | vendor 被锁 / WMI 失效 / 网络不可达 | 降级行为符合预期 | GP-1/7/14 |

**纪律**：涉及 marker / 恢复路径的改动，至少验收 normal + 1 条恢复路径。恢复路径验收必须**构造 marker 存在的初始状态**（不手动清理），直接触发恢复路径。

### 2.4.3 分层验收策略（alpha-1-pilot-round1-feedback.md L2488 实证 + VS Code 三层测试标杆）

> **目的**：将端到端验收拆分为分层验收，逻辑层独立闭合，下游独立 bug 不阻塞当前 bug 闭合。
> **实证**：GP-1 Turn 94 端到端验收暴露 gateway.asar 锁（GP-14）+ 渲染 crash（GP-13），导致 GP-1 无法闭合。分层验收后，GP-1 逻辑层 PASS，下游拆为独立 bug。

**分层标准**：

| 层 | 定义 | 验收方式 | 耗时 | 适用场景 |
|---|---|---|---|---|
| **单元层** | 纯逻辑，输入→输出，无外部依赖 | 临时目录 + 断言 | <1s | 守卫条件 / 比较逻辑 / 条件分支 |
| **组件层** | 单模块，需真实文件系统但不需进程间协作 | 真实 .7z + 7za + tmpdir | 2-5s | 文件操作 / 解压链路 / 目录扫描 |
| **集成层** | 多模块协作，需真实进程但不需完整启动 | 真实 spawn node + gateway | 5-10s | 跨进程协作 / 引擎启动 |
| **端到端层** | 真实双击 exe → /health 200 | 打包产物 + 完整环境 | 30s-2min | 完整启动链路 / 用户真实体验 |

**关键区分点**：
- 单元层 vs 组件层 = 要不要碰真实文件系统
- 组件层 vs 集成层 = 要不要启动子进程
- 集成层 vs 端到端层 = 要不要完整启动链路

**隔离原则**：
- 当前 bug 在单元层/组件层验证修复逻辑正确性即可闭合
- 端到端验收若失败，根因不在当前 bug 逻辑，而在下游独立问题，应作为独立 bug 调查，**不回滚当前修复**
- 每个修复必须标注分层归属，验收时按归属层执行，不盲目跑端到端

**与纪律 5 的关系**：纪律 5 要求"环境对等性审计不通过 = 不冻结"（覆盖降级/边界路径）。本节分层验收的隔离原则不覆盖纪律 5——逻辑层 PASS 可闭合当前 bug 的修复逻辑验证，但 Freeze 冻结门仍需环境对等性全通过。两者互补：分层验收管"修复逻辑对不对"，纪律 5 管"冻结门能不能过"。

### 2.4.4 Freeze vs Verify 能力边界（Turn 100 实证 + VS Code 三层测试标杆）

> **目的**：明确 Freeze 静态审计和 Verify 运行时验证各自的能力边界，避免过度信任 Freeze GO。
> **VS Code 标杆来源**：VS Code Release Wiki - Smoke Test（automated smoke）/ Endgame Testing（manual）/ Sanity Check（per-build verification）三层分层。

| 能发现的问题类型 | Freeze（静态） | Verify（运行时） | 实证 |
|---|---|---|---|
| 逻辑错误 / 架构违规 | ✅ | — | Turn 14 |
| 文件引用 / 缺漏 | ✅ | — | Turn 17 |
| 定义顺序 / import 时序 | ❌ | ✅ | Turn 100 |
| logging handler 配置 | ❌ | ✅ | Turn 100 |
| 运行时环境交互 | ⚠️（第7维度有限） | ✅ | GP-14 |
| 网络抖动 / 大文件上传 | ❌ | ✅ | Turn 91/93/97 |

**纪律**：Freeze GO ≠ 没问题。Verify 必须实际运行代码（禁止用 py_compile 代替运行时验证）。涉及定义顺序 / import 时序 / logging 配置的改动，Verify 必须实际执行脚本并检查输出。

### 2.4.5 Regression Test Card（VS Code Endgame Testing 标杆）

> **触发条件**：每个 GP bug 修复必须附 Regression Test Card，随 Freeze 提交。

每个 GP 修复必须包含：
1. **修复点验证**：修复的 bug 本身已验证修复（不只是 py_compile，要实际触发）
2. **Blast radius**：改动涉及哪些文件 / 哪些其他 GP 可能受影响
3. **相邻功能验证**：同文件 / 同链路的其他功能未破坏
4. **恢复路径验证**（如涉及清理/恢复）：normal + 1 条恢复路径

格式：

| 项 | 内容 |
|---|---|
| GP 编号 | GP-XX |
| 修复点 | <文件:行号 + 改动> |
| Blast radius | <受影响文件/GP> |
| 修复点验证 | <如何验证 + 结果> |
| 相邻功能验证 | <验证了什么 + 结果> |
| 恢复路径验证 | <如适用> |

### 2.4.6 客户端验收超时标准（Turn 85/91/97/102 实证）

> **目的**：消除 `Start-Process -Wait` 无限阻塞导致的"验收卡死"问题。

**禁止**：`Start-Process -Wait`（无限等待）。客户端启动涉及多进程链路（Electron → launcher.py → Python 后端 → OpenClaw Gateway），任一环节 hang 住都会导致永不返回。

**标准模式**：`Start-Process -PassThru` + 超时轮询 + 进程树终止

```powershell
# 标准客户端启动验收模式（禁止 Start-Process -Wait）
# 注意：$clientArgs 是显式变量，禁止用 $args（PowerShell 自动变量）
$clientArgs = @('--remote-debugging-port=9333')
$proc = Start-Process -FilePath $exePath -ArgumentList $clientArgs -PassThru
$timeout = 60  # 秒，根据场景调整
$elapsed = 0
while (-not $proc.HasExited -and $elapsed -lt $timeout) {
    Start-Sleep -Seconds 2
    $elapsed += 2
}
if (-not $proc.HasExited) {
    Write-Host "[TIMEOUT] 客户端 $timeout 秒未退出，强制终止进程树"
    # 注意：必须用 taskkill /T 杀进程树，Stop-Process 只杀主进程会留孤儿
    & taskkill /T /F /PID $proc.Id 2>$null
    # 超时不等于失败——客户端可能正在正常运行（如 CDP 验收需要客户端保持运行）
}
```

**超时参考表**：

| 验收场景 | 超时 | 说明 |
|---|---|---|
| NSIS 静默安装 `/S` | 120s | 大包（~250MB）解压 + Defender 首次扫描延迟 |
| 客户端启动 + 退出（验证崩溃） | 60s | 正常应 <30s，60s = 异常（Defender 可能加 10-20s） |
| 客户端启动 + CDP 验收（保持运行） | 30s 启动等待 | 30s 后检查 CDP 端口，不等退出 |
| vendor 解压（首次启动） | 180s | openclaw-runtime.7z 69.5MB 解压 |
| 后端 /health 就绪 | 30s | 轮询 /health，非阻塞等待 |

**纪律**：所有 `Start-Process` 验收必须带超时。超时后用 `taskkill /T /F` 杀进程树（非 `Stop-Process`）+ 记录日志 + 报告状态（超时 ≠ 失败，需判断客户端是否在正常运行）。

### 2.4.7 验证环境隔离（开发干扰防护）

> **触发条件**：所有涉及 CDP Playwright / API curl / 客户端启动的验证
> **行业对标**：VS Code Endgame Freeze（发布前 Feature Freeze，期间不引入新开发改动）
> **实证**：Turn 25 后端重启导致 A3 端点 404 / Turn 89 splash 修改时 CDP 截图不一致 / Turn 97 打包 + 验收并行卡住 / Turn 103 sync 后 bridge.py 路径变了

**规则**：
1. **CDP 端口隔离**：验证用 `--remote-debugging-port=9333`，独立于开发端口（9222）。验证专用端口不受开发窗口的后端重启影响
2. **验证期间后端不得重启**：/health 轮询失败 = 验证中断，标记为"环境干扰"，不标记为"验证失败"
3. **冻结窗口**：发布前 30 分钟为冻结窗口，禁止 `sync_from_dev` / `deploy_local` / `打包.bat`。冻结窗口内只做验证
4. **独立 user-data-dir**：验证用客户端使用独立 `--user-data-dir=$env:TEMP\verify-profile`，不受开发端配置污染

### 2.4.8 真安装验证（非 win-unpacked）

> **触发条件**：每次里程碑发版（alpha-N / beta-N / stable）+ 涉及 Electron main.js / installer.nsh / ASAR 打包的改动
> **行业对标**：VS Code Sanity Check——明确区分 System Installer / User Installer / Archive 三种形态，"安装步骤本身是被测试的一部分"
> **实证**：Turn 85/91/97/102/104 所有 CDP 验收都在 win-unpacked 里跑，从未验过 Program Files 真实安装。18 个 GP bug 均因仅测 win-unpacked 而未暴露 NSIS/ASAR/安装路径问题

**规则**：
1. **禁止 win-unpacked 作为唯一验收环境**：CDP 验证必须针对 `Setup.exe /S` 静默安装后的产物（`%LOCALAPPDATA%\Programs\Endless Agent\` 或自定义安装路径）
2. **验证内容**：安装 → ASAR 打包路径（`app.isPackaged === true`）→ 启动 → /health → Tab 切换 → 核心流程
3. **win-unpacked 仅用于快速冒烟**：开发阶段的快速验证可用 win-unpacked，但发版前必须跑真安装验证
4. **安装验证脚本**：随打包.bat 产物一起归档，作为 Sanity Check 的执行载体

**标准模式**：
```powershell
# 1. 静默安装
$installDir = "$env:TEMP\verify-install-$((Get-Date).ToString('yyyyMMddHHmmss'))"
& "dist\Endless Agent Setup.exe" /S /D=$installDir
# 2. 等待安装完成（轮询 exe 存在，超时 120s）
# 3. 启动已安装客户端（带 CDP 9333）
# 4. CDP 验证（连接 9333）
# 5. 清理（taskkill /T /F + Remove-Item）
```

### 2.4.9 发布门禁强制

> **触发条件**：每次执行 `发布.py`（deploy_push + upload_release）
> **行业对标**：VS Code Endgame Champion 角色 + Release Process 分支策略——"Sanity testing is the final verification process a build **must pass** before being released"
> **实证**：Turn 85/91/97/102/104 均跳过了打包后 Playwright 验证，发布门被当作"建议"而非"阻止"

**规则**：
1. **`发布.py` 执行前检查 `verification_results.json`**：文件存在 + 时效 ≤ 2h + `passed=true`。门禁不通过 = `发布.py` 拒绝执行（`exit 1`），不是 warning
2. **每次打包.bat 后 `verification_results.json` 失效**：打包产物变化 → 需重新验证
3. **`verification_results.json` 由真安装验证脚本生成**：验证通过后自动写入，包含 `verified_at` / `passed` / `scenarios_passed` / `scenarios_total` / `install_path_verified` / `build_version`
4. **落地时机**：纪律条款生效即需在 `发布.py` 中实现门禁检查代码（后续工作项）

### 2.4.10 开发环境盲区与 Defender 模拟验收

> **触发条件**：所有涉及 vendor 文件完整性 / sentinel 检查 / CodeSync 时序 / Electron 启动链路的 GP 修复
> **行业对标**：Chrome "ToT (Tree of Trust)" — Chrome 团队维护一份"开发环境与发布环境差异清单"，每次发布前逐项验证差异点不被破坏
> **实证**：alpha-1 第二轮小白鼠 GP-22/23A/23B/24 全部因开发环境与打包环境的结构性差异而无法在开发机发现。3 个小白鼠（liaowenbin / gzchenzixian / lianghengji）交叉验证确认 5 层差异

#### 小白鼠验收数据（alpha-1 第二轮实证）

| GP | 小白鼠 | 现象 | 开发机能否复现 | 根因 |
|----|--------|------|:------------:|------|
| GP-23A | 2 + 3 | GP-22 修复代码已同步但未生效 | ❌ | CodeSync 与 startBackend 并行 → Python 加载旧代码（开发机用 uvicorn 直接启动，不走 Electron bootSequence） |
| GP-23B | 2 | playwright-core 缺失 → Gateway import 失败 | ❌ | sentinel 不检查 node_modules（开发机 vendor 从 npm install，始终完整） |
| GP-22 | 2 | vendor/node 未被使用，fallback 到系统 PATH | ❌ | Defender 隔离 node.exe（开发机 vendor 目录已加 Defender 排除） |
| GP-24 | 3 | pip 缺失 → 依赖安装失败 | ❌ | 旧版 vendor 残留 + sentinel 不检查 pip（开发机用系统 Python，有 pip） |
| GP-25 | 2 + 3 | .env URL 错误（10.224.211.3 少 1） | ❌ | NSIS 不覆盖旧 .env（开发机 .env 手动维护） |

#### 差异存在的 5 层原因

开发环境跳过了打包环境的 **7 个启动步骤**，其中 4 个是 GP bug 的触发点：

```
开发环境启动路径（跳过 7 步）：
  uvicorn src.main:app --reload → Python 直接 import → 完成

打包环境启动路径（小白鼠真实路径）：
  双击 exe → Electron bootSequence
    → ensureVendor7z()           ← 开发机跳过（vendor 在 git 中）→ GP-22/23B/24
    → fetchClientConfig()        ← 开发机跳过
    → runCodeSync()              ← 开发机跳过（src/ 在项目目录）→ GP-23A
    → startBackend()             ← 开发机跳过（直接 uvicorn）→ GP-23A
      → ELECTRON_HANDLED_SYNC=1
      → _sync_dependencies_only() ← 开发机跳过 → GP-24
      → import src.main
    → waitForBackend()           ← 开发机跳过
    → createMainWindow()
```

| # | 差异维度 | 开发环境 | 打包环境 | 导致的 GP |
|---|---------|---------|---------|----------|
| 1 | 启动入口 | `uvicorn` 直接启动 | Electron bootSequence 多步骤 | GP-23A |
| 2 | CodeSync | 不走（src/ 在项目目录） | `ELECTRON_HANDLED_SYNC=1` | GP-23A |
| 3 | vendor 来源 | `git`/`npm install`（完整） | .7z 解压（Defender 可能隔离） | GP-22/23B/24 |
| 4 | Python 运行时 | 系统 Python（有 pip） | vendor embeddable | GP-24 |
| 5 | .env 文件 | 手动维护（正确） | NSIS 部署（不覆盖旧版） | GP-25 |

#### 最根本盲区：Defender 行为差异

**开发机的 Defender 行为与小白鼠的 Defender 行为不同**——这是无法在开发机模拟的环境差异：

- 开发机：vendor 目录在项目路径（如 `E:\Work\G112\...`），开发者长期使用，Defender 通常已加排除规则或已建立文件信誉
- 小白鼠：vendor 解压到 `%APPDATA%\Endless Agent\vendor\`，APPDATA 是 Defender **高敌意评分区域**（Roaming 目录 + 新写入的 exe + 未签名），node.exe（83MB 未签名）和 playwright-core 都可能被隔离

**为什么 §2.4.3 分层验收 + 纪律 5 环境对等性没有抓住**：分层验收的模拟方案（S1-S4）在开发机上跑——开发机的 Defender 不隔离开发目录的文件，所以"模拟 Defender 隔离"实际上是"删除文件后验证 sentinel 检测"，但 sentinel 检测通过后 Defender **可能再次隔离**重新解压的文件，这个竞态在开发机上无法复现。

#### 最优先改进：Defender 模拟验收（强制）

> **2026-07-03 Turn 117 修订**：本节原设计存在内在矛盾——同时承认"开发机无法模拟 Defender 行为"（L393）和"在开发机做 Defender 模拟验收"（原 L400-443）。Turn 116 实证：开发机 4 次 Defender 模拟验收全部失败（exit code=-1，根因 = Electron GPU 沙箱初始化失败，详见 `docs/releases/plans/gp-116-verify-retrospective.md` §七）。本节修订为四子节结构，消除内在矛盾。

##### §2.4.10.1 执行路径（按优先级，即时降级不重试）

| 优先级 | 路径 | 触发条件 | 脚本 |
|:------:|------|---------|------|
| 1 | **Windows Sandbox**（含真实 Defender） | 默认首选 | `scripts/defender-sim-sandbox.wsb` + `scripts/defender-sim-sandbox.ps1` |
| 2 | **Hyper-V 干净 Windows 11 VM** | Sandbox 不可用 = `Enable-WindowsOptionalFeature -FeatureName 'Containers-DisposableClientVM'` 返回非 0 OR 管理员权限被拒绝 OR `.wsb` 双击后 30s 内未出现 Sandbox 窗口 | 手动搭建 VM + 运行 `scripts/defender-sim-sandbox.ps1`（路径调整） |
| 3 | **开发机限制性验收**（标注为不完整覆盖） | VM 不可用 = Hyper-V feature 未启用 OR `New-VM` 失败 | 开发机运行 `scripts/defender-sim-sandbox.ps1`（加 `--disable-gpu` + `ELECTRON_ENABLE_LOGGING=1`） |

**开发机限制性验收的约束**：
- 仅验证 sentinel 组件层逻辑（V1-V7），**不验证端到端 Defender 行为**
- 结果标记为 `defender_coverage=incomplete`
- 每次使用需在 experiment-log 记录降级原因
- **`--disable-gpu` + `ELECTRON_ENABLE_LOGGING=1` 仅作用于开发机验证脚本；生产构建禁用**（生产侧 GPU 缓解走 §2.4.10.3 P1 观察项）

**标准模式**（Sandbox/VM 中执行）：
```powershell
# 1. 打包 win-unpacked（或使用已有产物，假设已就绪）
# 2. 模拟 Defender 隔离：删除 APPDATA vendor 关键文件
$vendorDir = "$env:APPDATA\Endless Agent\vendor"

# GP-22: 删除 node.exe
Remove-Item "$vendorDir\node\node.exe" -Force -ErrorAction SilentlyContinue
# GP-23B: 删除 playwright-core
Remove-Item "$vendorDir\openclaw-runtime\node_modules\playwright-core" -Recurse -Force -ErrorAction SilentlyContinue
# GP-24: 删除 pip
Remove-Item "$vendorDir\python-backend\Lib\site-packages\pip" -Recurse -Force -ErrorAction SilentlyContinue

# 3. 启动客户端（CDP 9333，超时 60s，Sandbox 不需要 --disable-gpu）
$proc = Start-Process -FilePath "dist\win-unpacked\Endless Agent.exe" `
    -ArgumentList '--remote-debugging-port=9333' -PassThru
# ... 超时轮询（§2.4.6 标准模式）...

# 4. 验证 sentinel 检测到缺失 → 触发重新解压
$launcherLog = Get-Content "$env:APPDATA\Endless Agent\data\launcher.log" -Encoding Default
$launcherLog | Select-String "files missing|re-extract|playwright-core|pip"

# 5. 验证重新解压后文件恢复
Test-Path "$vendorDir\node\node.exe"
Test-Path "$vendorDir\openclaw-runtime\node_modules\playwright-core\package.json"
Test-Path "$vendorDir\python-backend\Lib\site-packages\pip\__init__.py"

# 6. 清理
taskkill /T /F /PID $proc.Id
```

**验收标准**（可观测，适用于所有路径）：
- launcher.log 含 `files missing` + 被删除的文件名 → sentinel 检测到缺失 ✅
- launcher.log 含 `re-extract` → 触发重新解压 ✅
- 重新解压后 `Test-Path` 返回 `True` → 文件恢复 ✅
- server.log 无 `No module named pip` / `Cannot find package 'playwright-core'` → 后端正常启动 ✅

**成本**：+2min/验收。覆盖 GP-22/GP-23B/GP-24 三类 bug。

##### §2.4.10.2 结论标准（适用于所有路径）

- **exit code=-1 不接受"环境不稳定"结论**——必须用 Event Viewer / crash dump / ProcMon / `ELECTRON_ENABLE_LOGGING=1` 追查到可观测证据（Turn 116 教训：用"环境不稳定"搪塞未确定根因）
- Sandbox/VM 环境的验收结果优先级高于开发机
- 开发机限制性验收结果标注 `defender_coverage=incomplete`，不单独作为 Freeze 门禁通过依据（需配合组件层 V1-V7 验收）

##### §2.4.10.3 P1 观察项：app.disableHardwareAcceleration() 条件激活

**触发条件**：如果 2026-07-17（alpha-2 code freeze）前，有 ≥2 个独立开发/测试环境出现 Electron GPU 退出 exit code=-1（且 `--disable-gpu` flag 验证可行），则启动本方案。

**方案**：在 main.js 最顶部（`app.whenReady()` 之前）添加：
```javascript
if (app.isPackaged && process.platform === 'win32') {
  app.disableHardwareAcceleration();
}
```
仅在生产构建启用——开发环境继续保留 GPU 以检测回归。

**当前状态**：观察项，非本 Turn 范围。Turn 117 根因追查确认 exit code=-1 最可能原因为 GPU 沙箱初始化失败（8 项证据，`--disable-gpu` 验证测试通过），但 alpha-1 第二轮小白鼠未报告此问题（用户环境 GPU 配置不同）。

##### §2.4.10.4 与 §2.4.8 真安装验证的关系

§2.4.8 验证"安装步骤本身正确"（NSIS / ASAR / 安装路径），本节验证"vendor 文件完整性自愈"（sentinel 检测 + 重新解压）。两者互补：§2.4.8 管"装得对不对"，§2.4.10 管"装对了但文件丢了能不能自愈"。

### 2.4.11 待批量验收清单（pending-batch-verification.md）

> **触发条件**：GP 修复完成单元层+组件层验收，但端到端验收延后到批量打包时（如 launcher.py / main.js / installer.nsh 等部署链路文件需 sync_from_dev + 打包.bat 才能生效）。**纯业务逻辑改动**（Guidance / Pipeline / Render 等）不涉及打包，端到端验收走 `deploy_local` 或 API/CDP 验证，**不触发本节**——pending 文件不写入、不读取中断。
> **行业对标**：GitHub Projects "Pending Review" 列 + VS Code Endgame "Deferred Verifications" 看板——待办项有独立追踪通道，不依赖人记忆
> **实证**：Turn 127 GP-33 修复完成但端到端验收延后，待办信息分散在 feedback doc + experiment-log，新会话若只读 experiment-log 末尾会遗漏（Turn 128+ 覆盖末尾后 GP-33 待办不可见）

#### 文件定位

`docs/releases/pending-batch-verification.md` —— 所有"代码已修复，端到端验收待批量打包"GP 的集中索引。

**不是原始信息存储**——原始信息在 feedback doc（GP 修复记录章节）+ experiment-log（Turn 记录）。pending 文件只放"待办指针"，避免与 feedback doc 重复。

#### 维护规则

| 时机 | 动作 | 执行者 |
|------|------|--------|
| GP 修复完成，端到端验收延后 | 追加条目到 pending 文件（含 GP 编号 / 改动文件 / 已验收层 / 待验收项 / feedback doc 指针 / 验收步骤指针） | 主 Agent（Log 阶段） |
| 新会话激活 | 读 pending 文件，确认是否有待批量验收的 GP | OMO（§七激活流程） |
| 打包前 | 读 pending 文件，确认所有待验收 GP 都在本次打包范围内（或显式声明部分延后） | 主 Agent |
| 端到端验收完成 | **删除条目**（不归档——feedback doc + experiment-log 已是权威记录）+ 更新 feedback doc GP 状态为 ✅ 已闭合 | 主 Agent（Verify 阶段） |
| pending 文件为空 | 保留文件头说明，不删除文件 | — |

**为什么不归档**：feedback doc 是 GP 的权威记录（修复内容 + 验收结果 + 教训），experiment-log 是 harness 执行的权威记录（Turn 级过程）。pending 文件归档会与两者重复。待办完成即删除条目，保持文件简洁——空 = 无待验收，有内容 = 有待验收。

#### 条目格式

```markdown
### GP-XX：<简要描述>

| 项 | 值 |
|---|---|
| **状态** | ⏳ 代码已修复，端到端验收待批量打包 |
| **修复 Turn** | Turn XX |
| **改动文件** | <文件列表> |
| **已验收层** | 单元层 ✅ + 组件层 ✅（N/N PASS） |
| **待验收** | 端到端 E1/E2（<具体验收项>） |
| **详情** | feedback doc <路径> → "<章节名>" |
| **批量验收步骤** | feedback doc 同章节"批量验收待办清单"（N 步） |
| **阻塞发版** | 是（纪律 24） |
```

#### 与 §2.4.3 分层验收的关系

§2.4.3 定义"分层验收隔离"——逻辑层 PASS 可闭合修复逻辑验证。本节定义"端到端验收延后的追踪机制"——逻辑层 PASS 但端到端延后时，用 pending 文件确保不遗漏。两者互补：§2.4.3 管"修复逻辑对不对"，本节管"延后的端到端验收不丢失"。

### 2.5 Log

- **执行者**：独立记录 subagent（异步）+ 主 loop（事件投递）
- **记录到**：`docs/ovrt-doc-audit/experiment-log.md`
- **前置动作**：先读 experiment-log.md 末尾，确定下一个 Turn 编号（截至 2026-06-30 最新 Turn 62，下一个 = 63；新会话必须以实际读到的末尾 Turn 为准）

#### 记录架构（异步 subagent + 单写者）

```
主 loop（Sisyphus）
  │
  ├─ action 1 完成 → 投递事件到队列（内存操作，不等待）
  ├─ action 2 完成 → 投递事件到队列
  ├─ action 3 完成 → 投递事件到队列
  │
  └─ 不等待，继续下一步
                    │
                    ▼
        记录 subagent（异步，并行）
          从队列取事件 → 写入 experiment-log.md
```

- **主 loop 职责**：只投递事件到内存队列（action 描述 / 执行模型 / 耗时 / 备注），不写文件，不等待
- **记录 subagent 职责**：从队列消费事件，串行写入 experiment-log.md
- **单写者模式**：只有记录 subagent 写 experiment-log.md，主 loop 不碰该文件的写操作，避免并发写冲突
- **事件格式**：`{turn: XX, phase: "Plan/Freeze/Execute/Verify/Log", action: "<描述>", model: "<模型>", duration: "<耗时>", note: "<备注>", p0: <可选 P0 信息>}`

#### 记录时机（实时落盘，支持追溯与交叉比对）

记录不是 Turn 结束才写，而是**贯穿整个 loop 实时追加**。主 loop 投递事件后，记录 subagent 异步消费并写入：

| 时机 | 主 loop 动作 | 记录 subagent 写入内容 |
|---|---|---|
| **Plan 开始时** | 投递 Turn 骨架事件 | `### Turn XX — Phase 1: <标题>` + 维度表（Agent 行为/用户介入先填，决策质量填"待审计"）+ 空的"逐 Action 成本追踪"表头 |
| **每个 action 完成后** | 投递 action 事件 | 实时追加一行到"逐 Action 成本追踪"表：`\| N \| <Action> \| <执行模型> \| <耗时> \| <备注> \|` |
| **Phase 切换时** | 投递 Phase 切换事件 | 追加新 Phase 小节：`### Turn XX — Phase 2: <标题>` + 维度表 |
| **P0 发现时** | 投递 P0 事件（优先级最高，插队） | **立即**在当前 Turn 末尾追加 P0 记录块（不等 Turn 结束，因为 P0 会中断 loop 或回 Freeze） |
| **Log 阶段（Turn 结束）** | 投递汇总事件 | 补齐维度表的"决策质量"列 + "累计成本汇总"表 + "方法论观察" + 变更记录表（如本 Turn 引入方法论演进） |

**为什么异步 + 实时落盘**：
- **不占主 loop 等待时间**：主 loop 只做内存投递，记录 subagent 异步写文件，两者并行
- **追溯**：每个 action 完成后用户即可在 experiment-log.md 看到（记录 subagent 消费延迟 <1s），不用等 Turn 结束
- **交叉比对**：用户可随时拿 action 记录与其他 Turn 的同类 action 对比（如 Oracle 耗时趋势、explore 覆盖范围对比）
- **P0 不丢失**：P0 事件优先级最高，记录 subagent 优先消费写入；即使 P0 导致 loop 中断，已记录的 action 不会丢

#### 完整格式（对齐 experiment-log 既有结构）

```markdown
### Turn XX — Phase X: <标题>

| 维度 | 记录 |
|---|---|
| 执行模型 | <GLM 5.2 / OMO oracle / OMO momus / Sisyphus-Junior 等> |
| 并行调用 | <bg_xxx, 耗时, 任务描述>（无并行则填"无"） |
| Agent 行为 | <本 Turn 实际做了什么> |
| 用户介入 | <0 / 1 + 介入类型> |
| 决策质量 | <待审计 / 已审计 / P0/P1 数量> |

#### Turn XX — 逐 Action 成本追踪

| # | Action | 执行模型 | 耗时 | 备注 |
|---|---|---|---|---|
| 1 | <工具调用> | <模型> | <耗时> | <说明> |

#### P0 上报（如有）

| P0 # | 描述 | 来源 | 处理决策 |
|---|---|---|---|
| P0-1 | <描述> | Oracle / Momus / 主 Agent | <修复 / 升级晨珺 / 接受> |

#### 累计成本汇总（截至 Turn XX）

| 模型 | 调用次数 | 总耗时 | 成本等级 | 备注 |
|---|---|---|---|---|

> **方法论观察**：<本 Turn 的方法论洞察，如冻结门价值/成本分层/环境对等性发现>
```

- **环境对等性维度的审计/验证结果**：在"方法论观察"或独立小节记录
- **变更记录同步**：如本 Turn 引入方法论演进，同步更新 experiment-log 末尾"变更记录"表

#### 编码注意事项（纪律 18）

experiment-log.md 为 GBK 编码。记录 subagent 写入时：
- PowerShell `Add-Content` 不指定 `-Encoding`（默认 GBK）或显式 `-Encoding Default`
- 禁止 `-Encoding UTF8`（会叠加编码产生乱码）
- 读取时用 GBK 解码
- harness-protocol.md / .omo/plans/*.md / docs/releases/*.md 保持 UTF-8 编码

---

## 三、纪律条款（不可违反）

1. **Freeze / Verify 不可跳过**，无论改动大小（GP-3 Turn 49 教训：跳过 Freeze 后补做发现 31 个非 ASCII 字节）
2. **每个 Turn 记录执行模型 + 耗时**
3. **P0 立即上报**，不自行修复后继续；P0 立即落盘到 experiment-log（不等 Turn 结束）
4. **单轮冻结门不轻信**，修正后重新审计（Turn 45 教训）
5. **环境对等性审计不通过 = 不冻结**（GP-1/2/3 根因固化）
6. **部署链路文件必走冻结门**：installer.nsh（14 版本 bug 历史）/ launcher.py / main.js
7. **验收标准必须可观测**：指向具体日志行 / API 字段 / DOM 元素
8. **P1 ≤ 2 且有 mitigation 才可冻结**（对齐 experiment-log §1.3）
9. **Action 级实时落盘（异步 subagent）**：每个工具调用完成后，主 loop 投递事件到内存队列，独立记录 subagent 异步消费并写入 experiment-log.md 的"逐 Action 成本追踪"表。主 loop 不写文件、不等待，支持追溯与交叉比对
10. **确认无依赖后并行，不确定则串行**：每个 action 执行时，确认与其他 action 无数据/状态/文件依赖才并行；不确定是否有依赖则串行。已确认安全的并行：Plan 阶段 explore 搜索与读 experiment-log 末尾；Freeze 阶段 Oracle+Momus 双审；新会话激活时并行读两个文件。需约束的并行：Freeze R1 多 P0 修复（仅当不同文件且无逻辑依赖）；Execute DAG fan-out（同文件编辑必须串行）；Verify 前 3 项并行但环境对等性验证必须最后跑
11. **前端验收门禁不可跳过**（§2.1.5）：涉及前端 UI 改动时，必须先出单文件 HTML 验收稿，晨珺浏览器验证交互逻辑通过后，才进 Freeze / Execute。文字设计稿不算验收——必须可交互、可切换场景、可模拟操作
12. **代码必须遵守 `docs/deploy/README.md` 的规则**：该文档是热更部署与打包流程的开发者手册，包含多条用事故代价换来的硬规则。Execute 阶段任何涉及部署链路 / 打包 / 仓库同步的改动，Plan 草案必须显式核对以下条款，Freeze 阶段 Momus 完整性审计必须覆盖：
    - 🔴 **DEV/PKG 铁律**（§三 + §13.6）：所有源码修改必须在 DEV（`art-pipeline-agent`）进行，`sync_from_dev` 单向同步到 PKG（`endless-agent`）。PKG 的 `src/`、`ui-shell/`、`apps/client/` 等同步目录是 DEV 的**只读镜像**，直接修改会被下一次 `sync_from_dev --apply` 无条件覆盖。仅 `endless-agent/scripts/`（运维脚本）和 `resources/backend/`（种子数据）可在 PKG 直接改
    - ⚠️ **`deploy_local.py` 不可跳过**（§二 + §13.1）：推服务器前必须先本地验证（pkg → APPDATA 部署 + 自动清缓存 + 启动客户端冒烟）。教训：C7 模块拆分加载顺序错误导致 Tab 全部不可点击，有本地验证就能在推服务器前发现
    - 🔴 **服务器地址硬规则**（§十）：打包时 `.env` 必须将 `KNOWLEDGE_API_URL` 硬编码为当前唯一生产服务器地址（`http://10.224.211.13:8000`），不依赖 `redirect.json` 跳转，不烧录旧地址
    - 📋 **打包前置检查清单**（§九）：vendor Python 必须含 pip、vendor 必须带 Node.js、`打包.bat` 内置防御层（测试门禁 / 种子校验 / NSIS 语法预检 / winCodeSign / nsis-plugins）不可绕过
    - 📚 **发版事故记录**（§十三）：同类问题不出第二次。涉及 installer.nsh / launcher.py / main.js / theme-engine.js 等部署链路文件时，必须先翻阅事故记录确认未重蹈覆辙（如 `taskkill /T` 在自更新场景是毒药、module-level 函数不应依赖闭包变量、fetch 静态 JSON 必须加 cache-busting 等）
    - 📒 **ops log 台账双向引用**（`docs/distribution/distribution-pipeline-ops-log.md`）：ops log 是部署/打包领域的判例集（4835 行 / 257KB），与 §十三「发版事故记录」（13 条铁律）互补——§十三 是浓缩法条，ops log 是全量案例。三个维度：
        - **参考（Plan 阶段）**：改动涉及部署链路文件时，Plan 草案必须 grep 检索 ops log 历史教训（关键词匹配，非全量阅读——4835 行全量阅读成本不可接受），确认未重蹈覆辙。检索示例：改 `installer.nsh` → grep `installer`；改 `vendor` 相关 → grep `vendor`；改 `launcher.py` → grep `launcher`
        - **写入（Log 阶段）**：部署链路修复完成后，将结果追加到 ops log 末尾，记录格式对齐既有条目（背景 / 代码变更表 / 验收结果 / 教训）。**不重复 experiment-log 的过程记录**，只记结果，并反向引用 experiment-log 的 Turn 编号（如「详见 experiment-log Turn 66-70」）
        - **职责分工（防混淆）**：experiment-log = harness 执行**过程**（Turn 级、五阶段、Action 级实时落盘），ops log = 部署操作**结果**（操作级、代码变更 + 验收 + 教训）。两者通过 Turn 编号互相引用，不互相复制。已落地的范例：ops log 末尾 2026-06-30 vendor 目录占用修复条目——只记结果 + Oracle 安全评估 + 教训，过程引用 experiment-log Turn 66-70
    - **触发条件**：本条纪律在改动涉及 `apps/client/`、`launcher.py`、`installer.nsh`、`打包.bat`、`sync_from_dev.py`、`deploy_push.py`、`deploy_local.py`、`.env`、`config.py` 中服务器地址 / 盘符路径、或任何 `vendor_*` / `resources/` 目录时强制触发；纯 Guidance / Pipeline / Render 业务逻辑改动不触发
13. **验收不得绕过用户障碍**（GP-7 教训，2026-06-30）：Verify 阶段模拟用户场景时，**禁止手动执行用户不会做的操作来绕过障碍**。用户是美术，他们只会双击安装包、双击客户端图标——不会开 PowerShell 杀进程、不会手动删 APPDATA 目录、不会改注册表。如果修复的代码路径是"遇到障碍 → 自动清理 → 继续执行"，验收必须构造"障碍存在"的初始状态，然后**不手动清理**，直接触发修复路径，验证自动清理生效。
    - **反面案例**：GP-7 修复 cleanupStaleGateway/Python 后，开发者本机验收时手动杀进程 + 手动删 vendor 目录，然后启动客户端——绕过了"vendor 目录被锁"的障碍，验收"通过"。结果用户 lichen11 安装 1.0.85 时遇到同样的 vendor 锁定，因为用户不会手动杀进程删目录。修复"通过验收"但用户仍然遇到问题，直接降低用户信任度。
    - **正面做法**：构造障碍状态（如手动启动一个孤儿 python 进程占用 vendor 目录），然后**不手动清理**，直接启动客户端 / 双击安装包，验证 killAndCleanVendor 自动杀进程 + 自动删目录 + 正常启动。
    - **适用范围**：所有涉及"自动清理 / 自动修复 / 降级路径 / 故障自愈"的修复。验收的核心问题是"如果用户遇到这个障碍，修复能否自动解决"——手动绕过障碍等于没有验收。
    - **与纪律 5 的关系**：纪律 5 要求"环境对等性审计不通过 = 不冻结"（覆盖降级/边界路径）。本条纪律进一步要求"验收时不得手动绕过障碍"——即使环境对等性审计通过了（障碍场景已识别），验收时手动绕过障碍仍然等于无效验收。两者互补：纪律 5 保证"知道障碍存在"，纪律 13 保证"验证了障碍能自动解决"。
14. **Regression Test Card 强制**（VS Code 标杆）：每个 GP bug 修复必须附 Regression Test Card（§2.4.5），随 Freeze 提交。无 Card = Freeze 拒绝审计。Card 必须包含修复点验证 + blast radius + 相邻功能验证 + 恢复路径验证（如适用）
15. **打包验收路径矩阵强制**（§2.4.1）：改动涉及 Electron main.js / installer.nsh / launcher.py / resources/backend/ / vendor_* 时，必须按路径矩阵选择验收方式。禁止用手动 asar 重打包作为验收（Turn 41 实证不可靠）。deploy_local 不覆盖 main.js（Turn 87 实证）。Verify 前后必须清理 schtasks 残留任务 + marker 文件（Turn 101/102 实证）
16. **分层验收强制**（§2.4.3，alpha-1-pilot-round1-feedback.md L2488 实证）：每个 GP 修复必须标注分层归属（单元层/组件层/集成层/端到端层），验收时按归属层执行。端到端验收若失败且根因在下游独立问题，不回滚当前修复，下游拆为独立 bug。禁止盲目跑端到端验收当"万能验收"——端到端耗时 30s-2min 且暴露的下游问题会阻塞当前 bug 闭合（GP-1 Turn 94 教训）。**与纪律 5 的关系**：分层验收管"修复逻辑对不对"，纪律 5 管"冻结门能不能过"——逻辑层 PASS 可闭合修复逻辑验证，但 Freeze 仍需环境对等性全通过
17. **upload_release 网络重试标准 mitigation**（Turn 91/93/97 实证）：大文件上传 WinError 10054/10060 为已知网络抖动。重试 2 次（间隔 25-30s）。GBK emoji 问题：deploy_push.py 加 `sys.stdout.reconfigure(encoding='utf-8')`。409 Conflict = 已上传过（非错误）。deploy_push 成功 + /api/version 确认 = 代码已推送，upload_release 失败不阻塞验收
18. **文档编码规范**（Turn 97 教训 #5）：experiment-log.md 为 GBK 编码。追加内容用 GBK（PowerShell `Add-Content` 不指定 `-Encoding`）。禁止 `-Encoding UTF8`（会叠加编码产生乱码）。harness-protocol.md / .omo/plans/*.md / docs/releases/*.md 保持 UTF-8
19. **客户端验收超时强制**（§2.4.6）：禁止 `Start-Process -Wait`（无限等待）。所有客户端启动验收必须用 `-PassThru` + 超时轮询 + `taskkill /T /F` 杀进程树（非 `Stop-Process`）。超时后记录日志。超时 ≠ 失败（CDP 验收需客户端保持运行）。Turn 85/91/97/102 实证：`Start-Process -Wait` 导致验收卡死，需用户手动暂停
20. **用户作为纪律守门人**（Turn 94 实证）：harness-protocol 的纪律违规捕获以**用户纠正为权威信号**——用户指出"为什么 P0 降为 0 就直接进入执行"或"确认要走 R3 吗"时，Agent 必须立即停止当前流程，回退到用户指出的阶段重新审计。AI Agent 有效率优化倾向（跳过冻结门直接 Execute），harness-protocol 的"不轻信"原则与效率倾向存在结构性张力，用户纠正是唯一可靠的安全阀
21. **跨模块路径契约必须读代码验证**（GP-18 Turn 104 实证）：跨模块路径（如 gateway.pid 路径、state_dir 路径、getUserDataDir 路径）不能靠推理，必须读代码验证运行时路径解析。Oracle + Momus 可能对同一路径给出不同推荐（如 userDataDir/data/ vs state_dir），只有读代码确认 base_dir 解析逻辑才能解决。涉及路径的改动，Plan 阶段必须读代码确认路径解析链路
22. **GP 修复计划归档位置**：GP 修复计划放 `docs/releases/plans/gp-XX-fix-plan.md`（与 GP 文档在一起，利于归档）。`.omo/plans/` 只放 harness 协议级别的计划（如 harness-protocol 优化方案）。禁止 GP 修复计划散落在 `.omo/plans/` 中
23. **真安装验证强制**（§2.4.8）：禁止 win-unpacked 作为发版唯一验收环境。发版前必须跑 `Setup.exe /S` 静默安装 + CDP 验证。`app.isPackaged === true` 必须为真。Turn 85/91/97/102/104 实证：所有 CDP 验收都在 win-unpacked 里跑，18 个 GP bug 均因未验真实安装而未暴露
24. **发布门禁不可绕过**（§2.4.9）：`发布.py` 执行前必须检查 `verification_results.json`（存在 + 时效 ≤ 2h + passed=true）。门禁不通过 = `exit 1`。每次打包.bat 后验证结果失效。Turn 85/91/97/102/104 实证：发布门被当作"建议"跳过，5/5 次逃逸
25. **Defender 模拟验收强制**（§2.4.10）：涉及 vendor 文件完整性 / sentinel 检查 / CodeSync 时序 / Electron 启动链路的 GP 修复，Verify 阶段必须执行 Defender 模拟验收。**执行路径按优先级**（§2.4.10.1）：① Windows Sandbox（`scripts/defender-sim-sandbox.wsb`，含真实 Defender）→ ② Hyper-V 干净 VM（Sandbox 不可用时）→ ③ 开发机限制性验收（Sandbox+VM 均不可用，加 `--disable-gpu` + `ELECTRON_ENABLE_LOGGING=1`，标注 `defender_coverage=incomplete`，仅验证 sentinel 组件层 V1-V7）。**`--disable-gpu` 仅作用于开发机验证脚本；生产构建禁用**（生产侧 GPU 缓解走 §2.4.10.3 P1 观察项 `app.disableHardwareAcceleration()` 条件激活）。**结论标准**（§2.4.10.2）：exit code=-1 不接受"环境不稳定"结论，必须追查可观测证据。实证：alpha-1 第二轮 GP-22/23A/23B/24 全部因开发环境与打包环境 5 层结构性差异而无法在开发机发现；Turn 116 开发机 4 次 Defender 模拟验收全失败（exit code=-1，根因 = GPU 沙箱初始化失败）。成本 +2min/验收，覆盖 GP-22/23B/24 三类 bug。与 §2.4.8 互补：§2.4.8 管"装得对不对"，§2.4.10 管"装对了但文件丢了能不能自愈"

---

## 四、并行策略（对齐 experiment-log §1.4）

- **阶段内并行**：Freeze 阶段 Oracle + Momus 同时发射；Plan 阶段 explore 多路扇出
- **任务级并行**：Execute 按 DAG 批次 fan-out（如 experiment-log Turn 20 的 Wave 0 并行 4 任务）
- **跨阶段流水线**：Batch N Verify 与 Batch N+1 Execute 重叠（适用于多工作项场景）

---

## 五、模型配置（对齐 experiment-log §1.5）

| 角色 | 模型 | 用途 | 成本等级 |
|---|---|---|---|
| 主 Agent (Sisyphus) | GLM 5.2（netease-codemaker/glm-5.2） | 编排 + 决策 + 写作 | 中 |
| explore | OMO explore 模型 | 代码/文档搜索 | 低 |
| librarian | OMO librarian 模型 | 外部文档检索 | 低 |
| oracle | OMO oracle 模型 | 高质量推理审计 | 高 |
| momus | OMO momus 模型 | 计划评审 | 高 |
| metis | OMO metis 模型 | 意图分析 | 高 |
| task category: quick | category 优化模型 | 简单任务 | 低 |
| task category: deep | category 优化模型 | 复杂研究+实现 | 高 |
| task category: visual-engineering | category 优化模型 | 前端/UI | 中 |

**成本分层原则**：explore（低）做广度搜索，oracle/momus（高）做深度审计，GLM 5.2（中）做编排+验证。

---

## 六、实证依据

| 条款 | 实证来源 | 价值证明 |
|---|---|---|
| 冻结门双审 | experiment-log Turn 14 | 4 轮发现 10 P0，G-1 事实错误连源审计都遗漏 |
| 双层纠正 | experiment-log Turn 45-46 | R1 修正后仍引入新误判，R2 才抓到 |
| 环境对等性 | alpha-1-pilot-round1-feedback GP-1/2/3 | 开发环境正常路径偏置导致降级/边界路径从不验收 |
| 纪律不可跳过 | experiment-log Turn 49-51 | GP-3 跳过 Freeze 后补做发现编码定时炸弹 |
| 成本分层 | experiment-log §4.2 | explore(低)广度 → oracle/momus(高)深度 → GLM5.2(中)编排 |
| CDP 验收 | playwright-cdp-verification.md | 复用 Electron auth context，等同真人操作 |
| 审计模型轮换 | experiment-log §4.4 改进 1 | 同一模型可能共享盲区，R2 换 agent 类型提供正交视角 |
| 任务时长监控 | experiment-log §4.4 改进 2 | M1-10 运行 14min 异常长，需人工检查产出质量 |

---

## 七、新会话激活

新会话开始时，晨珺分发问题前应声明：

> 按 `docs/ovrt-doc-audit/harness-protocol.md` 执行

或直接在问题中引用本文件。OMO 收到后：

1. **并行读取**：harness-protocol.md 全文 + experiment-log.md 末尾（最后 2 个 Turn + 变更记录表）+ `docs/releases/pending-batch-verification.md`（待批量验收清单）——三者无依赖，同时启动
2. 确认五阶段纪律 + 冻结标准 + 环境对等性维度 + 当前 Turn 编号 + 最近的执行模式 + 方法论演进 + **是否有待批量验收的 GP**
3. 按本协议五阶段执行，不可裁剪
4. **Log 阶段**：执行记录追加到 experiment-log.md，Turn 编号接续（不重置）；若端到端验收延后，同步更新 pending-batch-verification.md（§2.4.11）

**不读 experiment-log 末尾的后果**：Turn 编号冲突 / 重复已验证的方法论 / 丢失上下文连续性。

**不读 pending-batch-verification.md 的后果**：待批量验收的 GP 被遗漏 / 发版门禁（纪律 24）被绕过 / 小白鼠安装未生效的修复。

---

## 变更记录

| 日期 | 变更内容 | 作者 |
|---|---|---|
| 2026-06-30 | 首版创建：基于 experiment-log 57 Turns 实证 + GP-1/2/3 环境对等性增强 | 晨珺 + Sisyphus |
| 2026-06-30 | 对齐 experiment-log：补齐架构审计轴 / P1 冻结标准 / 并行策略 / 模型配置 / 审计模型轮换 / 任务时长监控 | 晨珺 + Sisyphus |
| 2026-06-30 | 补齐双向引用：harness-protocol ↔ experiment-log；Log 格式完整化；Turn 编号连续性 | 晨珺 + Sisyphus |
| 2026-06-30 | 记录架构升级：异步 subagent + 单写者；Action 级实时落盘支持追溯与交叉比对 | 晨珺 + Sisyphus |
| 2026-06-30 | 并行审计：补齐 5 处遗漏（Plan/Freeze R1/Execute DAG/Verify 4 项/激活双读）+ 纪律条款 10「默认并行，除非有依赖」 | 晨珺 + Sisyphus |
| 2026-06-30 | 并行回退：纪律条款 10 改为「确认无依赖后并行，不确定则串行」；Freeze R1/Execute DAG/Verify 加约束条件（同文件串行/环境破坏最后跑） | 晨珺 + Sisyphus |
| 2026-06-30 | 新增 §2.1.5 前端验收门禁 + 纪律条款 11：涉及前端 UI 改动必须先出单文件 HTML 验收稿，晨珺验证通过后才进 Freeze/Execute。实证：UE4 连通引导任务先出文字设计稿用户要求看 HTML，出稿后发现布局顶出屏幕 | 晨珺 + Sisyphus |
| 2026-06-30 | 新增纪律条款 12：代码必须遵守 `docs/deploy/README.md` 的规则。覆盖 DEV/PKG 铁律、deploy_local 不可跳过、服务器地址硬规则、打包前置检查、发版事故记录。触发条件限定为部署链路 / 打包 / 仓库同步相关改动，纯业务逻辑改动不触发 | 晨珺 + Sisyphus |
| 2026-06-30 | 纪律条款 12 补充 ops log 台账双向引用子项：Plan 阶段 grep 检索历史教训（关键词匹配，非全量阅读），Log 阶段追加修复结果（不重复 experiment-log 过程，反向引用 Turn 编号）。划清 experiment-log（harness 过程）vs ops log（部署结果）职责边界 | 晨珺 + Sisyphus |
| 2026-06-30 | 新增纪律条款 13：验收不得绕过用户障碍。实证：GP-7 修复后开发者本机验收手动杀进程+删目录绕过障碍→验收"通过"→用户 lichen11 安装时遇到同样 vendor 锁定。与纪律 5（环境对等性）互补：纪律 5 保证"知道障碍存在"，纪律 13 保证"验证了障碍能自动解决" | 晨珺 + Sisyphus |
| 2026-07-02 | **P1 不收敛改进落地**（GP-14 Turn 99）：将 GP-14 P1 不收敛复盘的 4 项改进方向落地到 §2.2 Freeze 阶段。①修正者自审（新增子步骤，修正提交前对新代码做边界 case 自查，Oracle/Momus 将自审清单作为审计起点而非接受清单）②Momus 第 7 维度“运行时环境交互”（6→7 维度，覆盖 Defender/文件锁/进程时序/权限，与维度 3/5 互补）③P1 mitigation 质量标准（必须可验证，非 backlog；Verify 不可验证升级 P0）④P1 收敛趋势监控（多轮不收敛由 Momus 在 R3 触发专项分析，不阻塞冻结）。同步更新 §五 模型配置表 momus 行“完整性 6 维度”→“7 维度”。Freeze R1 双审：Oracle GO（P1=1 §五跨引用遗漏 + P2=3 文本增强）+ Momus OKAY，P1 修正后冻结。实证：GP-14 Turn 95 三轮冻结门 R1(4)→R2(2)→R3(2) 振荡，R2/R3 的 P0/P1 均在“修正引入的新代码”中发现——改进 ① 预计将三轮降为两轮（待验证假设） | 晨珺 + Sisyphus |
| 2026-07-02 | 打包验收优化：新增 §2.4.1-2.4.6（打包验收路径矩阵/多路径标准化/分层验收策略/Freeze vs Verify能力边界/Regression Test Card/客户端验收超时）+ 纪律条款 14-21 + §2.5 编码注意事项。实证：experiment-log Turn 1-104 + alpha-1-pilot-round1-feedback GP-1~18 打地鼠根因复盘 + L2488 分层验收策略吸收 + VS Code/Electron 业界标杆适配。Alpha 产品管理内容移至独立文档 docs/releases/alpha-process.md。Freeze R1 双审：Oracle CONDITIONAL GO（4 P0 修正：编号矛盾/§2.6移出/文件名/PowerShell缺陷）+ Momus REJECT（4 P0 修正：编号/V4-V6 grep/交叉引用/PowerShell $args+taskkill），主 Agent 自审 FREEZE GO | 晨珺 + Sisyphus |
| 2026-07-02 | 第二轮优化（Turn 106）：§2.1.5 修订（V7 Token 合规自证 + 生产级 CSS 保真）+ §2.1.5.1 新增（Stylelint CI 门禁，Momus 第 8 维度设计系统合规性）+ §2.2 修订（废除 P1≤2 豁免，改为 P0>0 OR P1>0 → MUST continue，行业对标 Google eng-practices + GitHub 二元模型）+ §2.2.1 新增（BADR 四步法：Benchmark-Adapt-Decide-Record，问题解决前行业对标强制）+ §2.4.7 新增（验证环境隔离：端口隔离/冻结窗口/独立 user-data-dir）+ §2.4.8 新增（真安装验证：禁止 win-unpacked 作为唯一验收，VS Code Sanity Check 标杆）+ §2.4.9 新增（发布门禁强制：verification_results.json 门禁，发布.py exit 1）+ 纪律条款 22-24。行业标杆：VS Code Sanity Check / Endgame Champion / Google eng-practices / Stylelint / Google SRE postmortem / Atlassian retrospective。实证：Turn 85/91/97/102/104 打包后验收全逃逸 + GP-5 13 个 V2 违规 + GP-11 简化 mockup + §2.2 freeze 逻辑歧义 | 晨珺 + Sisyphus |
| 2026-07-03 | §2.1.5 引用补充：新增 `preview-prototype-protocol.md`（交互稿制作协议），定义"完全按照生产环境复刻"的 6 步流程 + 4 类常见陷阱（data-theme 错位 / CSS 类冲突 / 颜色多源 / 缺框架）+ 验证清单。实证：case-rollout module-1 车辆原画交互稿 4 轮修正——①弹窗界面→页面流 ②缺主体框架→完整 Pipeline Tab ③颜色不一致→以实际运行界面为准 ④data-theme 放 html→放 body。根因：从源码反推界面而非对标实际运行界面 | 晨珺 + Sisyphus |
| 2026-07-03 | **Defender 模拟验收落地**（GP-23 Turn 112）：新增 §2.4.10（开发环境盲区与 Defender 模拟验收）+ 纪律条款 25。实证来源：alpha-1 第二轮 3 个小白鼠（liaowenbin / gzchenzixian / lianghengji）交叉验证——GP-22/23A/23B/24 全部因开发环境与打包环境 5 层结构性差异（启动入口 / CodeSync / vendor 来源 / Python 运行时 / .env）而无法在开发机发现。记录小白鼠验收数据表（5 个 GP × 开发机能否复现 × 根因）+ 5 层差异原因 + 最根本盲区（Defender 行为差异：开发目录已加排除 vs APPDATA 高敌意区域，无法在开发机模拟）+ 最优先改进（Defender 模拟验收：打包 win-unpacked → 手动删除 vendor 关键文件 → 验证 sentinel 检测 + 重新解压，成本 +2min，覆盖 GP-22/23B/24）。行业对标：Chrome ToT (Tree of Trust) 差异清单。与 §2.4.8 互补：§2.4.8 管"装得对不对"，§2.4.10 管"装对了但文件丢了能不能自愈" | 晨珺 + Sisyphus |
| 2026-07-03 | **§2.4.10 修订消除内在矛盾**（Turn 117）：Turn 116 开发机 4 次 Defender 模拟验收全失败（exit code=-1），复盘发现 §2.4.10 存在内在矛盾（同时承认"无法在开发机模拟 Defender"和"在开发机做 Defender 模拟验收"）。Turn 117 根因追查（8 项证据）确认 exit code=-1 最可能原因为 Electron 28.3.3 GPU 沙箱初始化失败（`--disable-gpu` 验证测试通过 25s 无退出）。修订内容：①§2.4.10 重构为四子节（§2.4.10.1 执行路径三优先级即时降级 / §2.4.10.2 结论标准所有路径适用 / §2.4.10.3 P1 观察项 disableHardwareAcceleration 条件激活 / §2.4.10.4 与 §2.4.8 关系）②纪律 25 同步更新（执行路径按优先级 + `--disable-gpu` 仅开发机 + 生产禁用）③新增 `scripts/defender-sim-sandbox.wsb` + `scripts/defender-sim-sandbox.ps1`。Freeze 两轮：R1 Oracle CONDITIONAL GO（7 P1）+ Momus NEEDS REVISION（1 P0 纪律 25 同步 + 3 P1）→ R2 Metis CONDITIONAL GO（1 P0 自审表 + 4 P1 歧义）+ Explore 事实核查（7/10 VERIFIED）。实证：`docs/releases/plans/gp-116-verify-retrospective.md` §七 8 项证据 + `docs/ovrt-doc-audit/experiment-log.md` Turn 116-117 | 晨珺 + Sisyphus |
| 2026-07-06 | **待批量验收清单机制**（Turn 127）：新增 §2.4.11（pending-batch-verification.md）+ §七新会话激活流程更新（并行读 3 文件：harness-protocol + experiment-log 末尾 + pending-batch-verification）。维护规则：GP 修复完成端到端延后时追加条目，验收完成后删除条目（不归档——feedback doc + experiment-log 已是权威记录）。行业对标：GitHub Projects "Pending Review" 列 + VS Code Endgame "Deferred Verifications" 看板。实证：Turn 127 GP-33 修复完成但端到端验收延后，待办信息分散在 feedback doc + experiment-log，新会话若只读 experiment-log 末尾会遗漏（Turn 128+ 覆盖末尾后 GP-33 待办不可见）。pending 文件只放"待办指针"不存原始信息，避免与 feedback doc 重复 | 晨珺 + Sisyphus |
