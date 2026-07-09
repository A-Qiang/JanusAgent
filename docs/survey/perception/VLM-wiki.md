# VLM-wiki 仓库总结

> **仓库地址**: [https://github.com/VeniVeci/VLM-wiki](https://github.com/VeniVeci/VLM-wiki)
> **Stars**: 11 (截至 2026-07)
> **语言**: Python (98.4%), PowerShell (1.3%), Batchfile (0.3%)
> **License**: MIT

---

## 概述

VLM-wiki 是一个基于 **Karpathy LLM Wiki** 思想构建的**全模态个人知识库**系统。其核心创新在于将原本仅支持文本的 LLM Wiki 扩展为支持图片、视频、音频、文本多种模态输入，利用 **VLM（视觉语言模型）+ LLM（语言模型）** 的协同来理解和组织知识。Wiki 本身是一个持久化、持续累积的个人知识库。

---

## 核心理念

| 原则 | 说明 |
|------|------|
| **多模态摄入** | 支持图片、视频、音频、文本全方位记录，不局限于纯文本 |
| **VLM + LLM** | 用视觉语言模型理解图像/视频内容，用语⾔模型整理知识 |
| **Markdown 优先** | 所有内容以标准 Markdown 存储，可被任意编辑器/工具使用 |
| **持续累积** | Wiki 是持久化的、不断复合的个人知识库，随时间增值 |
| **原始数据不变** | `raw/` 下的源材料只读不修改，确保数据完整性 |

---

## 项目架构

### 三层结构

```
project/
├── raw/                      # [源材料层] 只读，不可修改
│   ├── images/ YYYY-MM/     # 照片、截图
│   ├── videos/ YYYY-MM/     # 视频 + 字幕 / 音轨
│   ├── audio/  YYYY-MM/     # 语音备忘录
│   ├── text/   YYYY-MM/     # 文本文档
│   └── diary/                # 日记条目
│
├── wiki/                     # [知识层] VLM/LLM 维护的文章
│   ├── index.md             # 全局索引（每篇文章一行，按分类分组）
│   ├── log.md               # 追加式操作日志
│   ├── moments/             # 人生重要时刻
│   ├── people/              # 人物
│   ├── places/              # 地点
│   ├── projects/            # 项目
│   ├── concepts/            # 概念与想法
│   ├── patterns/            # 发现的生活模式
│   └── archives/            # 综合分析 / 回忆录
│
├── .vlmwiki/                 # [配置层]
│   └── config.json          # 模型 & 设置配置 (支持 config.local.json 覆写)
│
├── references/               # 模板文件
│   ├── raw-template.md
│   ├── article-template.md
│   ├── archive-template.md
│   └── index-template.md
│
├── scripts/                  # Python 分析脚本
│
└── AGENTS.md                 # Agent 操作规范
```

### 核心数据流

```
源材料(raw/) ──→ VLM 分析 ──→ 信息提取(人物/时间/地点/活动/情绪) ──→ Wiki 文章更新 ──→ 模式发现
                              ↑                                          ↓
                        LLM 辅助整理                              反射引擎生成回顾
                                                                       ↓
                                                                企业微信推送
```

---

## 关键技术组件

### 1. 媒体摄入管线

| 媒体类型 | 处理流程 |
|---------|---------|
| **图片** | VLM 分析内容 → 提取元数据(EXIF日期/位置/人物/活动) → 生成描述 → 存入 `raw/images/YY-MM/` → 更新 wiki |
| **视频** | 提取关键帧(始/中/末/场景切换) → 转录音频 → VLM 描述视觉内容 → 生成摘要 → 更新 wiki |
| **音频** | 语音转文字 → 识别主题/情感/关键点 → 生成摘要 → 更新 wiki |
| **文�文本** | 解析日期、人物、地点、话题 → 更新 wiki 对应分类 |
| **日记** | 同文本处理，额外支持情感趋势分析 |

### 2. 分析脚本 (`scripts/`)

| 脚本 | 功能 |
|------|------|
| `video_extractor.py` | 视频抽帧，提取关键帧和场景变化 |
| `image_analyzer.py` | 图片元数据分析（EXIF、GPS 等） |
| `qwen_vlm_analyzer.py` | 基于 Qwen 模型的 VLM 多模态分析 |
| `run_analysis_now.py` | 立即执行一次完整分析 |
| `import_data_sources.py` | **外部数据源导入器**：手机相册/备忘录/幕布日记等自动导入 `raw/`；通过 `import_manifest.json` 去重 |
| `reflection_engine.py` | **反射/回顾引擎**：从 `wiki/` + `raw/diary/` 合成历史信号，生成每日/每周回顾 + 下一步建议 |
| `work_project_reflection.py` | **工作项目扫描器**：扫描工作目录 → 生成 `wiki/projects/` 页面 → 发企业微信推送 |
| `run_work_reflection_cycle.py` | 单次"扫描 + 推送"循环 |
| `wecom_push.py` | 企业微信推送适配器（支持群机器人 webhook 和自建应用消息两种模式） |

### 3. 模型配置

支持多种 VLM/LLM 提供商，通过 `.vlmwiki/config.json` 配置：

```json
{
  "vlm": {
    "provider": "openai | gemini | claude | ollama",
    "model": "gpt-4o | gemini-pro-vision | claude-3-sonnet | llava",
    "api_key_env": "OPENAI_API_KEY | GEMINI_API_KEY | ANTHROPIC_API_KEY"
  },
  "llm": {
    "provider": "openai | anthropic | ollama | local | ide",
    "model": "gpt-4o | claude-3-sonnet | qwen2"
  }
}
```

**关键设计**：
- 若未配置模型，自动使用 IDE 内置模型（如 Trae IDE 的 MiniMax-M2）
- 本机敏感配置通过 `config.local.json` 单独管理，不提交到 git

### 4. 外部数据源导入机制

`import_data_sources.py` 支持的源类型：

| 类型 | 说明 |
|------|------|
| `photo_album` | 照片/视频导入 `raw/images/` 和 `raw/videos/` |
| `note_export` | 备忘录导入 `raw/text/` |
| `mubu_diary` | 幕布日记导入 `raw/diary/` |
| `generic_text` / `generic_diary` / `generic_audio` / `generic_video` | 通用类型 |

具备**导入去重**能力，依赖 `import_manifest.json` 避免重复导入相同文件。

### 5. 反射引擎 (Reflection Engine)

生成三大类输出：
1. **Snapshot**: 当前记忆库概览（moments/places/diary/media 统计）
2. **What History Says**: 历史倾向分析（主题/地点/日记线索）
3. **Recommended Next Actions**: 下一步应补充的素材和页面类型

每周回顾自动通过企业微信推送给用户。

---

## 实现状态评估

> 基于对仓库全部 7 个 commit、17 个 Python 脚本、配置文件、模板和 wiki 内容的逐一审查。

### ✅ 已实现的特性

| 类别 | 特性 | 说明 | 代码质量 |
|------|------|------|---------|
| **基础设施** | 项目骨架搭建 | raw/wiki/.vlmwiki/references 完整目录结构，含模板 | ✅ 完整 |
| **配置** | 模型配置体系 | config.json + config.local.json 双层配置，支持 OpenAI/Gemini/Claude/Ollama | ✅ 完整 |
| **数据导入** | `import_data_sources.py` | 外部数据源导入器：支持 photo_album/note_export/mubu_diary 等 8 种类型，含去重 Manifest | ⭐ 高质量, 约 300 行, 结构良好 |
| **图片基本分析** | `image_analyzer.py` | 读取图片尺寸/格式/色彩模式（基于 Pillow） | ⚠️ 基础, 仅元数据层面, 无 EXIF/GPS/内容理解 |
| **VLM 图片分析** | `qwen_vlm_analyzer.py` | 集成 Qwen 3.5 Omni Flash 模型，通过 OpenAI 兼容接口分析图片内容 | ✅ 可用, 硬编码部分路径 |
| **VLM 推理演示** | `run_analysis_now.py` | 单张图片分析命令行工具 | ⚠️ 硬编码 Windows 路径 |
| **视频抽帧** | `video_extractor.py` | 基于 OpenCV 的视频关键帧提取 | ⚠️ 基础, 硬编码路径 |
| **反射引擎** | `reflection_engine.py` | 从 wiki/ + raw/diary/ 生成 Snapshot/历史分析/下一步建议，可输出日/周回顾 | ⭐ 高质量, ~400 行, 架构清晰 |
| **工作项目扫描** | `work_project_reflection.py` | 扫描本地工作目录，识别活跃项目和文件变更，生成项目页和回顾 | ⭐ 高质量, ~500 行, 含 git 集成 |
| **运行包装** | `run_work_reflection_cycle.py` | 单次"扫描+推送"循环入口 | ✅ |
| **Windows 脚本** | `run_work_reflection_task.ps1/.cmd` | Windows 计划任务入口 | ✅ |
| **企业微信推送** | `wecom_push.py` | 支持 webhook 和自建应用两种模式的消息推送 | ✅ 完整, 含异常处理 |
| **Wiki 内容** | demo 数据 | 青岛旅行相关内容（2 条 moment, 6 条 place, log 记录） | ✅ 演示级 |
| **配置工具** | `config_utils.py` | 配置加载辅助函数 | ✅ |

### ⏳ 部分实现 / Demo 级别

| 特性 | 现状 | 说明 |
|------|------|------|
| **自动 Wiki 文章生成** | ❌ **未实现** | 虽然 qwen_vlm_analyzer.py 能分析图片内容，但**没有任何脚本自动将 VLM 分析结果转换为 wiki 文章**。wiki 中的优质内容(如 Places/青岛)是人工/IDE Agent 编写的 |
| **图文分析→入库流水线** | ❌ **未打通** | 分析脚本的输出只是分析结果的 md/txt，没有对接 wiki 文章创建逻辑 |
| **EXIF 信息提取** | ❌ **未实现** | config.json 中 `extract_exif: true`，但 image_analyzer.py 完全不读 EXIF 数据 |
| **VLM 分析结果的实际使用** | ⚠️ **不连贯** | `update_vlm_docs.py`（90 行的小脚本）的功能是给手动创建的 "模拟分析文档" 加免责声明 —— 证实早期结论一直是手工而非真实 VLM 产出的 |

### ❌ README 中提到但实际未实现的特性

| 声称的特性 | 实际状态 | 证据 |
|-----------|---------|------|
| **自动视频转录** (auto_transcribe_video) | ❌ **完全未实现** | video_extractor.py 只有抽帧功能，没有任何音频转录代码 |
| **自动音频转录** (auto_transcribe_audio) | ❌ **完全未实现** | scripts/ 中没有音频处理相关脚本。raw/audio/ 为空目录 |
| **模式发现** (pattern_discovery) | ❌ **完全未实现** | AGENTS.md 描述了 5 类自动化模式检测（时间/人物/地点/情绪/学习模式），但无一实现。reflection_engine.py 的手工统计/推荐接近但远未达"模式发现"程度 |
| **Agent 触发命令** (`add image/video/audio`, `what do I know about`, `analyze my patterns`, `today in history`) | ❌ **仅为设计文档** | AGENTS.md 中定义的这些指令是**给人类用户在 AI IDE 中使用的工作流说明**，没有任何对应的可执行代码。它们是 agent 行为规范，不是软件功能 |
| **提醒推送** (`reminder_enabled`, `reminder_time`) | ❌ **关闭(disabled)** | config.json 中默认 `reminder_enabled: false`，无调度守护进程 |
| **音频文件格式支持** (mp3/m4a/wav/ogg/flac/aac) | ❌ **无对应处理代码** | 虽然 config.json 中配置了格式列表，但没有处理它们的脚本 |
| **图片"人物/活动识别"** | ❌ **未实现** | image_analyzer.py 仅提取尺寸/格式，不做任何语义理解。唯一能理解内容的 qwen_vlm_analyzer 是人类手动调用分析单个图片的 |
| **自动情感趋势分析** | ❌ **未实现** | 只在 reflection_engine.py 中有简单的 keyword_counts_from_diaries（词频统计），没有真正的情绪分析 |

### 🔧 代码质量评价

```
import_data_sources.py       ⭐⭐⭐⭐  高质量, 结构清晰, 导入去重逻辑完善
reflection_engine.py         ⭐⭐⭐⭐  充分模块化, dataclass + 类型标注, 关注点分离
work_project_reflection.py   ⭐⭐⭐⭐  多目录扫描, git 集成, 自动生成项目页
wecom_push.py                ⭐⭐⭐⭐  鲁棒性强, 异常处理完善, 支持双模式
qwen_vlm_analyzer.py         ⭐⭐⭐   功能性可用, 但 main 块含硬编码 Windows 路径
config.json                  ⭐⭐⭐⭐  精心设计的配置结构, 注释完善
image_analyzer.py            ⭐⭐     仅基础 PIL 读取, 远低于 README 声称的能力
video_extractor.py           ⭐⭐     仅抽帧, 硬编码路径, 无 YAML 错误处理
update_vlm_docs.py           ⭐⭐     90 行的权宜脚本, 反映早期无真正 VLM 结果的临时方案
run_analysis_now.py          ⭐⭐     硬编码 Windows 绝对路径, 不可迁移
```

### 📊 实现覆盖率估算

| 维度 | 覆盖率 | 说明 |
|------|--------|------|
| **项目骨架** | 95% | 目录、模板、配置基本完整 |
| **数据导入** | 90% | import_data_sources.py 较完善 |
| **图片分析** | 30% | 仅有基础元数据 + 手动 VLM 调用，无自动流程 |
| **视频处理** | 15% | 仅实现了抽帧，转录/分析/摘要均缺失 |
| **音频处理** | 0% | 完全没有实现 |
| **文本/日记** | 25% | reflection_engine 能读取日记进行统计 |
| **Wiki 文章生成** | 10% | 无自动从分析结果创建文章的脚本 |
| **模式发现** | 0% | 仅字面描述，无算法实现 |
| **Agent 命令** | 5% | 仅定义为 AGENTS.md 规范，无可执行代码 |
| **通知推送** | 90% | wecom_push.py 完整可用 |
| **反射回顾** | 85% | reflection_engine + work_project_reflection 较完整 |

> **综合判断**: 这是一个 **MVP 验证阶段**的项目。README/规划描述了全套全模态个人知识管理的雄心，但实际代码覆盖了约 **30-40%** 的规划能力。最成熟的是基础设施（导入、反射、推送）；最关键缺失是**自动 Wiki 文章生成流水线**和**音频/模式发现**两大核心能力。

---

## Agent 交互模式（设计说明）

> ⚠️ **以下命令均为 AGENTS.md 中定义的设计规范，没有对应的可执行代码**。它们描述了用户在 AI IDE（如 Trae、Cursor）中应如何与 AI Agent 交互。软件本身没有命令行入口或 API 端点来实现这些命令。

仓库的 AGENTS.md 定义了一组**触发命令**的交互规范：

| 命令 | 功能 | 实现状态 |
|------|------|---------|
| `add image [path]` | 将图片添加到 wiki | ❌ 无代码实现，仅为 Agent 行为规范 |
| `add video [path]` | 将视频添加到 wiki | ❌ 同上 |
| `add audio [path]` | 将音频添加到 wiki | ❌ 同上 |
| `what do I know about [topic]` | 查询已有知识 | ❌ 同上 |
| `analyze my patterns` | 分析生活模式 | ❌ 同上 |
| `today in history` | 回忆每年今日 | ❌ 同上 |
| `generate reflection` | 生成今日回顾与明日建议 | ⚠️ 有 reflection_engine.py 脚本，但无 CLI 命令集成 |
| `push review to wecom` | 推送到企业微信 | ⚠️ 有 wecom_push.py 脚本，但无 CLI 命令集成 |

---

## 与 Karpathy LLM Wiki 对比

| 特性 | LLM Wiki | VLM Wiki |
|------|---------|----------|
| 文本处理 | ✅ | ✅ |
| 图片理解 | ❌ | ✅ |
| 视频分析 | ❌ | ✅ |
| 音频处理 | ❌ | ✅ |
| 多模态关联 | ❌ | ✅ |
| 生活模式发现 | 基础 | 深度 |
| 企业微信推送 | ❌ | ✅ |
| 外部数据导入 | ❌ | ✅ |
| 自动回顾生成 | ❌ | ✅ |

---

## 综合评价

### 优势
1. **前瞻的架构设计**: 三层分离(源材料/知识/配置)的目录组织和 AGENTS.md 行为规范是一套合理的设计蓝图
2. **高质量的基础设施脚本**: import_data_sources(数据导入)、reflection_engine(反思引擎)、work_project_reflection(工作扫描)三个脚本的质量足以投入实际使用
3. **实用的企业微信集成**: wecom_push.py 支持 webhook 和自建应用，是企业环境中实用的远程推送通道
4. **真实的 VLM 集成证明**: qwen_vlm_analyzer.py 证明了通过 OpenAI 兼容接口可以真实调用 VLM 模型分析图片，demo 留存的 wiki 文章也展示了落地的可能性
5. **良好的可扩展性**: 清晰的模块划分，支持多种 VLM/LLM 后端，留出充足的定制空间

### 局限
1. **承诺高于交付**: README 描绘了完整的全模态流水线，但实际代码覆盖率约 30-40%，核心"媒体分析→自动 Wiki 文章生成"流水线缺失
2. **音频处理为零**: 声明的音频转型/处理能力完全没有实现
3. **视频能力极基础**: 仅实现了 OpenCV 抽帧，没有真正的视频分析(场景理解/转录/摘要)
4. **无 CLI/GUI 入口**: 没有一个统一的命令行入口或用户界面，所有脚本需分别手动调用，距离"自动化知识管家"还有差距
5. **平台绑定**: 仅支持企业微信(WeCom)
6. **单人业余项目**: 7 个 commit，硬编码路径，大量 Windows 特定假设，零测试
7. **隐私无保障**: 图片须上传至云端 API (Qwen/OpenAI)，没有本地模型推理的支持证据

### 对我方项目的借鉴意义

VLM-wiki 项目的设计理念和部分组件值得参考：

1. **`raw/` → `wiki/` 的数据分层思想**: 原始材料不变 + 知识固化沉淀的良好分离模式
2. **导入去重机制**: manifest 文件的 file_fingerprint(SHA1) 校验方案可以直接复用
3. **反射引擎设计**: reflection_engine 的 "Snapshot + What History Says + Recommended Next Actions" 三段式回顾输出适合我们的调研展示场景
4. **避免踩坑**: VLM-wiki 项目中"全通话但没有打通流水线"的问题提醒我们 —— 核心价值在于端到端的自动化，而不是孤立的点状脚本

### 适用场景
- 作为**全模态个人知识仓库的架构参考**
- import_data_sources 的思路可直接复用到类似的数据接入场景
- reflection_engine 的 review 生成模式适合调研报告的自动化产出
- 不适用于需要开箱即用全模态知识管理系统的场景
