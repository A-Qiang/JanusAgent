# MinerU Backend 差异详解

> 基于 MinerU v3.4 README 及源码分析，整理于 2026-07-20

## 一、Backend 总览

MinerU 提供 **5 种解析后端**，分为三大类：

| 类别 | 后端名称 | 核心特点 |
|------|---------|---------|
| **pipeline** | `pipeline` | 传统多模型 OCR 管线，兼容性好，支持纯 CPU |
| **\*-engine** | `vlm-engine` | 本地 VLM 模型推理引擎，高精度 |
| | `hybrid-engine` | 管线布局 + VLM 抽取的混合引擎，高精度 + 低幻觉（默认后端） |
| **\*-http-client** | `vlm-http-client` | 通过 OpenAI 兼容 API 连接远程 VLM 服务 |
| | `hybrid-http-client` | 通过 OpenAI 兼容 API 连接远程 VLM 服务 + 本地小模型 |

## 二、各 Backend 详细解析

### 1. pipeline — 传统多模型 OCR 管线

**工作原理：**

Pipeline 后端采用经典的"多原子模型串联"架构，通过多个专用小模型依次完成文档解析的各子任务：

```
PDF/图片 → 版面检测(Layout) → 公式检测(MFD) → 公式识别(MFR) → OCR识别 → 表格识别 → 中间JSON → Markdown
```

**使用的原子模型**（源码 `model_list.py` + `model_init.py`）：

| 原子模型 | 用途 | 具体模型 |
|---------|------|---------|
| Layout | 版面布局检测 | PP-DocLayoutV2 |
| MFD | 公式检测 | 内置检测模型 |
| MFR | 公式识别 | Unimernet (small) / PP-FormulaNet-Plus-M（中文公式优化） |
| OCR | 文字识别 | PyTorchPaddleOCR (PP-OCRv6，v3.4升级) |
| Table (Wired/Wireless) | 表格识别 | SLANet-Plus / UNet-Table |
| TableCls | 表格类型分类 | PaddleTableCls |
| TableOrientationCls | 表格方向分类 | MineruTableOrientationCls |

**关键特性：**
- 无幻觉（hallucination-free），所有输出均来自模型检测和识别
- 支持纯 CPU 运行，最低 4GB VRAM
- OmniDocBench v1.6 准确率：**86.47**
- 支持 `auto/txt/ocr` 三种解析方法
- 支持多语言 OCR（109 种语言）
- v3.4 中 OCR 模型升级为 PP-OCRv6，准确率提升约 11%，处理速度提升约 100%
- 已移除 AGPLv3 模型（doclayoutyolo、mfd_yolov8）和 CC-BY-NC-SA 4.0 模型（layoutreader）

**适用场景：** 资源受限环境、纯 CPU 部署、对幻觉零容忍的场景、大批量简单文档处理

---

### 2. vlm-engine — 本地 VLM 推理引擎

**工作原理：**

VLM 后端使用单一的视觉语言模型（Vision-Language Model）直接对文档页面进行端到端理解和结构化输出，无需多模型串联。当前使用模型为 **MinerU2.5-Pro-2605-1.2B**（v3.3 升级）。

```
PDF/图片 → VLM 模型直接输出结构化内容（文本/公式/表格/图片描述等）→ 中间JSON → Markdown
```

**支持的本地推理后端**（源码 `vlm_analyze.py`）：

| 推理后端 | 说明 |
|---------|------|
| `vllm-engine` | 使用 vLLM 同步引擎，支持 logits processor 优化 |
| `vllm-async-engine` | 使用 vLLM 异步引擎，适合高并发场景 |
| `lmdeploy-engine` | 使用 LMDeploy（pytorch/turbomind），支持 Ascend/Camb 等国产芯片 |
| `mlx-engine` | 使用 Apple MLX 框架，仅支持 macOS Apple Silicon |
| `transformers` | 使用 HuggingFace Transformers，兼容性最好 |

**关键特性：**
- 高精度：OmniDocBench v1.6 准确率 **95.30**
- 支持图片/图表分析、截断段落合并、跨页表格合并、表格内图片识别
- 原生多语言 OCR 支持（v3.3 新增）
- 不支持纯 CPU 运行，最低 8GB VRAM
- GPU 要求：Volta 架构及以上或 Apple Silicon
- 需要本地下载模型文件（约 20GB 磁盘空间）

**适用场景：** 有 GPU 资源、追求最高精度的单模型方案、复杂文档（含图片/图表/跨页表格）

---

### 3. hybrid-engine — 混合引擎（默认后端）

**工作原理：**

Hybrid 后端是 Pipeline 和 VLM 的融合方案，结合了两者的优势：
- 使用 **Pipeline 的小模型**进行版面布局检测（Layout）和公式检测（MFD/OCR-det）
- 使用 **VLM 模型**进行内容抽取（文本识别、表格结构化、图片分析等）
- 对文本型 PDF 支持原生文本提取（native text extraction），降低幻觉

```
PDF/图片 → Pipeline Layout检测 + 公式检测 → VLM 基于布局信息抽取内容 → 中间JSON → Markdown
```

**effort 解析强度参数**（v3.3 新增）：

| effort 模式 | 工作方式 | 精度 | 速度 | 图片分析 |
|------------|---------|------|------|---------|
| `medium`（默认） | Pipeline 布局检测 → VLM `batch_extract_with_layout` | 95.26 | 快 35%~220% | 不支持 |
| `high` | VLM `batch_two_step_extract`（两步抽取） | 95.39 | 较慢 | 支持 |

**medium 模式的核心逻辑**（源码 `hybrid_analyze.py` L965-1004）：
1. Pipeline 小模型完成 Layout 检测和表格方向分类
2. 将 Layout 结果映射为 VLM Block 类型
3. VLM 基于 Layout 提供的布局信息进行 `batch_extract_with_layout`（带布局的批量抽取）
4. 公式区域交由 Pipeline 的 MFR 模型识别
5. 强制关闭图片/图表分析以保持快速路径

**high 模式的核心逻辑**（源码 L1005-1033）：
1. VLM 直接执行 `batch_two_step_extract`（两步抽取：先布局后内容）
2. 支持 OCR-det 侧车信息补充
3. 支持图片/图表分析
4. 公式区域同样交由 Pipeline MFR 模型识别

**关键特性：**
- 最高精度：OmniDocBench v1.6 准确率 **95.39**（high）/ **95.26**（medium）
- 原生文本提取 → 低幻觉
- 不支持纯 CPU 运行，最低 8GB VRAM
- medium 较 high 在不同平台提速 35%~220%（文本 PDF 场景：Linux 80%↑, Windows 90%↑, macOS 220%↑）
- v3.0 起为默认后端

**适用场景：** 有 GPU 资源、追求最高精度且需要控制速度的通用场景、文本型 PDF（利用原生文本提取降低幻觉）

---

### 4. vlm-http-client — 远程 VLM 客户端

**工作原理：**

与 vlm-engine 使用相同的 VLM 模型和算法，但模型推理不在本地进行，而是通过 OpenAI 兼容 API 发送到远程服务器。

```
PDF/图片 → 本地预处理 → HTTP请求 → 远程 VLM 服务器(vLLM/SGLang/LMDeploy) → 返回结果 → 中间JSON → Markdown
```

**关键特性：**
- 精度与 vlm-engine 完全一致：**95.30**
- 客户端支持纯 CPU 运行（推理在服务端）
- 最低 2GB VRAM（客户端仅做预处理）或不需要 GPU
- 磁盘仅需 2GB（无需下载模型文件）
- 通过 `-u/--url` 指定 OpenAI 兼容服务地址
- 通过 `MINERU_VL_MODEL_NAME` 指定模型名称
- 通过 `MINERU_VL_API_KEY` 进行身份验证
- 支持 `max_concurrency`、`http_timeout`、`max_retries` 等客户端参数

**适用场景：** 边缘设备部署、集中式推理服务（多客户端共享 GPU）、轻量级客户端部署

---

### 5. hybrid-http-client — 远程 Hybrid 客户端

**工作原理：**

Hybrid 的客户端版本：
- Pipeline 小模型（Layout、MFD、OCR-det）在**本地**运行
- VLM 内容抽取通过 **HTTP 请求**发送到远程服务器

```
PDF/图片 → 本地Pipeline(Layout+MFD+OCR-det) → HTTP请求 → 远程VLM抽取 → 返回结果 → 中间JSON → Markdown
```

**关键特性：**
- 精度与 hybrid-engine 完全一致：**95.39**（high）/ **95.26**（medium）
- 客户端支持纯 CPU 运行（VLM 推理在服务端，小模型可在 CPU 运行）
- 最低 2GB VRAM（用于本地小模型推理）
- 支持 `MINERU_HYBRID_BATCH_RATIO` 环境变量控制本地小模型 batch 倍率，按显存调整：

  | 客户端显存 | 推荐 batch_ratio |
  |-----------|-----------------|
  | ≤ 6 GB | 8 |
  | ≤ 4 GB | 4 |
  | ≤ 3 GB | 2 |
  | ≤ 2 GB | 1 |

- 支持 `effort` 参数（medium/high）
- 磁盘仅需 2GB（VLM 模型在服务端）

**适用场景：** 边缘设备部署且追求高精度、分布式部署（小模型本地 + VLM 集中）、需要灵活控制客户端显存占用

---

## 三、横向对比总表

### 硬件与资源需求

| 指标 | pipeline | vlm-engine | hybrid-engine | vlm-http-client | hybrid-http-client |
|------|----------|------------|---------------|-----------------|-------------------|
| 纯 CPU 支持 | ✅ | ❌ | ❌ | ✅ | ✅ |
| GPU 加速 | Volta+ / Apple Silicon | Volta+ / Apple Silicon | Volta+ / Apple Silicon | Volta+ / Apple Silicon | 不需要（VLM 在远端） |
| 最低 VRAM | 4GB | 8GB | 8GB | 2GB | 2GB |
| 最低 RAM | 16GB（推荐 32GB+） | 16GB（推荐 32GB+） | 16GB（推荐 32GB+） | 16GB | 16GB |
| 最低磁盘 | 20GB（SSD 推荐） | 20GB（SSD 推荐） | 20GB（SSD 推荐） | 2GB | 2GB |
| 操作系统 | Linux/Win/macOS | Linux/Win/macOS | Linux/Win/macOS | Linux/Win/macOS | Linux/Win/macOS |

### 精度与性能

| 指标 | pipeline | vlm-engine | hybrid-engine | vlm-http-client | hybrid-http-client |
|------|----------|------------|---------------|-----------------|-------------------|
| OmniDocBench v1.6 | 86.47 | 95.30 | 95.39(high) / 95.26(medium) | 95.30 | 95.39(high) / 95.26(medium) |
| 幻觉风险 | 无 | 较高 | 低（原生文本提取） | 较高 | 低（原生文本提取） |
| 图片/图表分析 | ❌ | ✅ | ✅（仅 high 模式） | ✅ | ✅（仅 high 模式） |
| 解析方法选择 | auto/txt/ocr | — | auto/txt/ocr | — | auto/txt/ocr |
| 语言指定 | ✅（`-l` 参数） | — | — | — | — |
| effort 参数 | — | — | medium/high | — | medium/high |
| 默认后端 | ❌ | ❌ | ✅（v3.0+） | ❌ | ❌ |

### 架构差异

| 维度 | pipeline | vlm-engine | hybrid-engine |
|------|----------|------------|---------------|
| 布局检测 | Pipeline 小模型(PP-DocLayoutV2) | VLM 内部完成 | Pipeline 小模型(PP-DocLayoutV2) |
| 文字识别 | PaddleOCR (PP-OCRv6) | VLM 直接输出 | VLM 抽取 + Pipeline OCR-det 补充 |
| 公式识别 | Unimernet / PP-FormulaNet | VLM 直接输出 | Pipeline MFR(Unimernet) |
| 表格识别 | SLANet / UNet-Table | VLM 直接输出 | VLM 抽取 |
| 图片分析 | ❌ | VLM 直接输出 | VLM（仅 high 模式） |
| 原生文本提取 | ❌（全部走 OCR） | ❌（全部走 VLM） | ✅（文本型 PDF 直接提取） |

---

## 四、选型决策树

```
是否需要最高精度？
├── 是 → 是否有本地 GPU (≥8GB VRAM)？
│   ├── 是 → 对幻觉敏感？
│   │   ├── 是 → hybrid-engine (effort=high) ✅ 推荐
│   │   └── 否 → vlm-engine
│   └── 否 → 是否有远程 VLM 服务？
│       ├── 是 → hybrid-http-client (effort=high) ✅ 推荐
│       └── 否 → 需要搭建远程服务或使用 pipeline
│
└── 否 → 是否只有 CPU / 资源受限？
    ├── 是 → pipeline ✅ 推荐
    └── 否 → 需要平衡速度与精度？
        ├── 是 → hybrid-engine (effort=medium) ✅ 推荐（默认）
        └── 否 → pipeline
```

## 五、命令行使用示例

```bash
# pipeline 后端（纯 CPU 可用）
mineru -p input.pdf -o output/ -b pipeline

# vlm-engine 后端（需 GPU）
mineru -p input.pdf -o output/ -b vlm-engine

# hybrid-engine 后端，medium 强度（默认，速度优先）
mineru -p input.pdf -o output/ -b hybrid-engine --effort medium

# hybrid-engine 后端，high 强度（精度优先，支持图片分析）
mineru -p input.pdf -o output/ -b hybrid-engine --effort high

# vlm-http-client 后端（连接远程 VLM 服务）
mineru -p input.pdf -o output/ -b vlm-http-client -u http://localhost:8000/v1

# hybrid-http-client 后端（本地小模型 + 远程 VLM）
mineru -p input.pdf -o output/ -b hybrid-http-client -u http://localhost:8000/v1 --effort high
```

## 六、国产 AI 芯片支持

pipeline 和 vlm-engine/hybrid-engine 均支持国产 AI 芯片加速：

| 芯片 | 支持方式 |
|------|---------|
| 昇腾 Ascend | LMDeploy (pytorch backend) |
| 平头哥 T-Head | 专用适配 |
| 沐曦 METAX | 专用适配 |
| 海光 Hygon | 专用适配 |
| 燧原 Enflame | 专用适配 |
| 摩尔线程 MooreThreads | 专用适配 |
| 天数智芯 IluvatarCorex | 专用适配 |
| 寒武纪 Cambricon | LMDeploy (pytorch backend) |
| 昆仑芯 Kunlunxin | 专用适配 |
| 壁仞 Biren | 社区贡献 |
| 太初元碁 Tecorigin | 社区贡献 |

---

## 七、总结

| 后端 | 一句话定位 |
|------|-----------|
| **pipeline** | 兼容性王者，纯 CPU 可跑，零幻觉，适合资源受限和简单文档 |
| **vlm-engine** | 精度标杆，单模型端到端，适合复杂文档和有充足 GPU 的场景 |
| **hybrid-engine** | 最佳平衡，管线布局 + VLM 抽取 + 原生文本提取，默认首选 |
| **vlm-http-client** | 轻量客户端，精度不缩水，适合边缘设备和集中式部署 |
| **hybrid-http-client** | 分布式最优解，本地小模型 + 远程 VLM，灵活控制显存 |

**推荐默认选择：** `hybrid-engine --effort medium`（v3.0+ 默认后端），在绝大多数场景下提供了精度和速度的最佳平衡。仅在纯 CPU 环境或需要零幻觉时切换到 `pipeline`。
