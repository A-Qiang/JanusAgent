# MinerU — 高精度文档解析引擎调研报告

> **仓库地址**: [https://github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)
> **最新版本**: v3.4.3 (2026-07)
> **Stars**: 38k+ (截至 2026-07)
> **License**: MinerU Open Source License (基于 Apache 2.0 的自定义许可)
> **论文**: arXiv:2409.18839 / arXiv:2509.22186 / arXiv:2604.04771
> **开发商**: OpenDataLab (上海人工智能实验室)

---

## 1. 概述

MinerU 是一款面向 **LLM / RAG / Agent** 工作流的高精度文档解析引擎，最初诞生于 [InternLM](https://github.com/InternLM/InternLM) 预训练过程中的符号转化需求。它能够将 PDF、图片、DOCX、PPTX、XLSX 等多种格式的非结构化文档转换为结构化的 Markdown / JSON 格式，供下游检索、抽取与二次处理使用。

### 定位

MinerU 不是简单的 OCR 工具或 PDF 转文本工具——它是一个**全格式、多后端的结构化文档理解系统**，覆盖从文档解析、版面分析、公式识别、表格重建到输出渲染的完整 pipeline。

| 维度 | MinerU |
|------|--------|
| 输入格式 | PDF, Image, DOCX, PPTX, XLSX |
| 输出格式 | Multimodal/NLP Markdown, JSON (阅读序), 中间格式 |
| 语言支持 | 109 种语言 OCR |
| 后端种类 | pipeline / vlm-engine / hybrid-engine / office |
| 部署方式 | CLI / FastAPI / Gradio WebUI / Docker / Desktop |
| 国产算力 | 昇腾、寒武纪、燧原、沐曦、摩尔线程、昆仑芯等 10+ |

---

## 2. 核心架构

### 2.1 总体分层

```
User Interface Layer (CLI / API / Gradio / Router)
        │
        ▼
Backend Orchestration Layer (backend/)
     ┌────┼────┬────┐
     │    │    │    │
  pipeline  vlm  hybrid  office
  (纯CV)  (VLM) (CV+VLM) (原生)
        │
        ▼
Data Abstraction Layer (data/)
  ┌────────┴────────┐
  data_reader_writer/    io/
  (文件/内存/S3)          (HTTP/S3)
        │
        ▼
Model Layer (model/)
  layout/   ocr/   mfr/   table/   vlm/
  (版面)   (OCR)  (公式)  (表格)   (VLM Server)
```

### 2.2 CLI 工具矩阵

| 命令 | 功能 |
|------|------|
| `mineru` | 编排客户端，自动拉起本地服务或连接远程 API |
| `mineru-api` | FastAPI 服务，支持同步(`POST /file_parse`)和异步(`POST /tasks`)接口 |
| `mineru-router` | 多服务/多 GPU 统一入口网关，支持自动负载均衡 |
| `mineru-gradio` | Gradio WebUI |
| `mineru-vllm-server` | vLLM 推理后端启动器 |
| `mineru-lmdeploy-server` | LMDeploy 推理后端启动器 |
| `mineru-openai-server` | OpenAI 兼容 API 服务启动器 |
| `mineru-models-download` | 模型下载工具 |

---

## 3. 四大解析后端

### 3.1 Pipeline 后端 (`backend/pipeline/`)

**定位**: 快速稳定、零幻觉、支持纯 CPU 运行

**核心流程**:
```
PDF/Image → layout detection → OCR → formula recognition → table recognition → merge → Markdown/JSON
```

**关键技术**:
- **版面分析**: PP-DocLayoutV2 — PaddleOCR 系深度学习版面检测模型
- **OCR**: PP-OCRv6 — 最新版 PaddleOCR 模型，109 种语言
- **公式识别**: UniMERNet (默认) 或 PP-FormulaNet-Plus-M
- **表格识别**: SLANet-Plus 或 UNet-Table
- **表格分类**: Paddle-Table-Cls + Mineru-Table-Orientation-Cls

**精度**: 86.47 (OmniDocBench v1.6 E2E)

**亮点**:
- 滑动窗口机制解析上万页文档，无需手动拆分
- batch 推理支持流式落盘
- 多线程并发推理安全

**内部模型管理器** (`model_init.py`):
```python
class MineruPipelineModel:
    # 统一管理所有原子模型实例
    # 包含: layout_model, mfr_model, ocr_model, table_models...
    # 通过 AtomModelSingleton 实现模型级别单例
```

### 3.2 VLM 后端 (`backend/vlm/`)

**定位**: 基于视觉语言模型的最优精度，但需要 GPU

**核心流程**:
```
PDF pages → image rendering → VLM (Qwen2-VL) → parse structured output → Merge
```

**关键技术**:
- **主模型**: `MinerU2.5-Pro-2605-1.2B` (基于 Qwen2.5-VL 微调的专用文档解析 VLM)
- **推理后端支持**:
  - `transformers` — 原生 PyTorch 推理
  - `vLLM` — 高性能推理，支持 PagedAttention
  - `LMDeploy` — TurboMind 推理引擎
  - `mlx` — Apple Silicon 优化
  - `http-client` — OpenAI 兼容 API 客户端

**精度**: 95.30 (vlm-engine, OmniDocBench v1.6)

**特点**:
- 结构化 JSON 输出（直接描述文档版面、公式、表格）
- 原生支持多语言 OCR
- 支持图片/图表分析 (`image analysis`)
- 等待延迟比 pipeline 高 (需 GPU 推理)

### 3.3 Hybrid 后端 (`backend/hybrid/`)

**定位**: VLM + Pipeline 融合，取二者之长

**核心思路**:
```
Page → pipeline(layout+OCR+MFR) → layout boxes → VLM(layout-guided) → merge
```

**精髓**: Pipeline 先做版面分析 + OCR + 公式检测得出准确的边界框，然后将这些框送入 VLM 做结构化理解。这样 VLM 只需要"看图说话"（描述每个区域的内容类型），不需要自己做版面检测。

**Effort 强度机制**:

| 档次 | 精度 | 速度提升 | 支持 image analysis | 适用场景 |
|------|------|----------|---------------------|----------|
| `medium` (默认) | 95.26 | 35%~220% 快 | ❌ | 日常文档处理 |
| `high` | 95.39 | 基准 | ✅ | 极致精度需求 |

**速度对比 (medium vs high)**:
- Linux 文本 PDF: ~80% 快; Linux OCR: ~35% 快
- Windows 文本 PDF: ~90% 快; Windows OCR: ~45% 快
- macOS 文本 PDF: ~220% 快; macOS OCR: ~50% 快

### 3.4 Office 后端 (`backend/office/`)

**定位**: DOCX/PPTX/XLSX 原生解析（不需转 PDF）

**三个子模块**:
- `docx_analyze.py` — 解析 DOCX，提取文本、图片、表格、公式、列表、目录
- `pptx_analyze.py` — 解析 PPTX，提取幻灯片内容、图表结构
- `xlsx_analyze.py` — 解析 XLSX，读取电子表格结构和数据

**关键优势**:
- 相比先转 PDF 再解析，端到端速度提升 **数十倍**
- 无 VLM/OCR 幻觉
- 原生保留格式信息（字体、颜色、样式等）
- 依赖 python-docx / pypptx-with-oxml / openpyxl / mammoth

---

## 4. 模型生态

### 4.1 模型家族（MinerU 系列 VLM）

| 版本 | 参数量 | 技术报告 | 特点 |
|------|--------|----------|------|
| MinerU 1.0 | ~0.9B | arXiv:2409.18839 | 初始版本，基于 InternVL |
| MinerU 2.0-2505 | 0.9B | — | 被 pipeline 86.2 分超越 |
| MinerU 2.5 | — | arXiv:2509.22186 | 解耦式 VL，高效高分辨率解析 |
| MinerU 2.5-Pro-2604 | 1.2B | — | 支持图片/图表解析、跨页表格合并 |
| MinerU 2.5-Pro-2605 | 1.2B | arXiv:2604.04771 | 最新版，修复多 Bug，原生多语言 OCR |
| MinerU-Diffusion | — | arXiv:2603.22458 | OCR 逆渲染扩散解码方法 |

### 4.2 原子模型（Pipeline / Hybrid 依赖）

| 类别 | 模型 | 路径 (ModelPath) | 用途 |
|------|------|-------------------|------|
| **版面** | PP-DocLayoutV2 | `models/Layout/PP-DocLayoutV2` | 版面元素检测（文本/表格/图片/公式/页眉页脚等） |
| **OCR** | PaddleOCR Torch | `models/OCR/paddleocr_torch` | 文字检测与识别 (~109 语言) |
| **公式** | UniMERNet Small | `models/MFR/unimernet_hf_small_2503` | 公式识别 (LaTeX) |
| **公式 (备选)** | PP-FormulaNet-Plus-M | `models/MFR/pp_formulanet_plus_m` | 中文公式专用 (环境变量 `MINERU_FORMULA_CH_SUPPORT`) |
| **表格** | SLANet-Plus | `models/TabRec/SlanetPlus` (ONNX) | 表格结构恢复 |
| **表格 (备选)** | UNet-Table | `models/TabRec/UnetStructure` (ONNX) | 表格结构恢复 |
| **表格方向** | PP-LCNet-x1.0 | `models/TabCls/` (ONNX) | 表格方向分类 |
| **VLM** | MinerU2.5-Pro-2605-1.2B | HuggingFace/ModelScope | VLM 后端主模型 |
| **Pipeline Kit** | PDF-Extract-Kit-1.0 | HuggingFace/ModelScope | Pipeline 模型集合 |

### 4.3 模型下载与管理

MinerU 实现了自动模型下载与缓存系统:

1. 自动选择模型源（HuggingFace / ModelScope），首次安装时检测网络环境
2. 优先检查本地缓存，命中则直接复用
3. 支持通过 `MINERU_MODEL_SOURCE` 环境变量切换源
4. 通过 `mineru-models-download` 命令提前下载

**模板配置文件** (`mineru.template.json`):
```json
{
  "models-dir": { "pipeline": "", "vlm": "" },  // 自定义模型路径
  "model-source": "auto",   // huggingface/modelscope/auto
  "llm-aided-config": {...},  // 可选的 LLM 辅助标题润色
  "config_version": "1.3.2"
}
```

---

## 5. 部署与集成

### 5.1 系统需求

| 维度 | Pipeline | VLM-Engine | Hybrid-Engine | HTTP-Client |
|------|----------|-------------|---------------|-------------|
| GPU VRAM | 4GB+ | 8GB+ | 8GB+ | 不要求 (远端 GPU) |
| RAM | 16GB+ (推荐 32GB+) | 16GB+ (推荐 32GB+) | 16GB+ (推荐 32GB+) | 16GB+ |
| 磁盘 | 20GB+ (SSD) | 20GB+ (SSD) | 20GB+ (SSD) | 2GB+ |
| Pure CPU | ✅ | ❌ | ❌ | ✅ |
| 多 OS | Linux/Win/macOS | Linux/Win/macOS | Linux/Win/macOS | 任意 |

### 5.2 使用方式

**CLI 基础用法**:
```bash
# 单个文件
mineru -p input.pdf -o ./output

# 批量目录
mineru -p ./docs/ -o ./output/

# 指定纯 CPU pipeline 后端
mineru -p input.pdf -o ./output -b pipeline
```

**API 异步任务**:
```bash
# 提交任务
curl -X POST http://localhost:8012/tasks \
  -F "file=@document.pdf" \
  -F "parse_options={\"backend\":\"hybrid\"}" \

# 查询状态
curl http://localhost:8012/tasks/{task_id}

# 获取结果
curl http://localhost:8012/tasks/{task_id}/result
```

**Router 多 GPU 负载均衡**:
```bash
mineru-router --worker-urls http://gpu1:8012,http://gpu2:8012
```

### 5.3 集成方案

| 场景 | 方式 |
|------|------|
| **AI 编程工具** | MCP Server — Cursor / Claude Desktop / Windsurf |
| **RAG 框架** | LangChain / LlamaIndex / RAGFlow / Dify / FastGPT |
| **Python SDK** | `pip install mineru[all]` |
| **Go / TypeScript** | REST API (JSON) |
| **无代码** | mineru.net 在线版 / Desktop 客户端 |

### 5.4 资源需求分析（转型成本）

| 维度 | 成本 |
|------|------|
| **GPU 推理服务** | 单卡 A10/4090 可运行 Hybrid medium，8GB 显存起 |
| **纯 CPU 部署** | pipeline 后端，精度 ~86，4GB 最少，无需 GPU |
| **离线部署** | 模型总量 ~20GB 磁盘空间 |
| **国产算力** | 昇腾/寒武纪/燧原等 >10 款已适配 |

---

## 6. 技术亮点

### 6.1 输出质量保障

- **页眉/页脚/页码自动去除**: 版面分析阶段识别 header/footer/page_number 类型并丢弃
- **阅读顺序排序**: 输出按人类自然阅读顺序排列（从左到右、从上到下），而非物理位置序
- **跨页表格合并**: 检测分布在多页的同一表格，自动拼接
- **截断段落合并**: VLM 检测被分页截断的段落并合并
- **多栏布局适配**: 复杂版面布局自动识别左右分栏关系

### 6.2 长文档处理

- **滑动窗口**: pipeline 后端通过滑动窗口控制每批次处理页数，峰值内存可控
- **流式落盘**: batch 推理过程中完成后立即写出已解析结果
- **线程安全**: 全链路线程安全，支持多线程并发推理

### 6.3 DLL 命名约定

整个代码库采用清晰的类层级命名规范:

```
magic_model  — 统一内容模型层 (各种后端的 MagicModel 化一格式)
middle_json  — 中间 JSON 表示
model_json_to_middle_json — 模型原始输出 → 中间 JSON
mkcontent    — 最终输出生成 (Markdown/ContentList 等)
```

---

## 7. 在 JanusAgent 中的定位

```
perception-agent/ (JanusAgent 多模感知层)
       │
       ├── MinerU/ ← 本文档
       │     └── 高精度文档解析引擎 (PDF/Image/Office → Markdown/JSON)
       │
       └── (其他 Perception Provider)
             └── 图片/音频/视频处理器等
```

### 与 JanusAgent 的潜在结合点

1. **Knowledge Ingestion Pipeline**: MinerU 可作为文档摄入的默认实现，将 PDF/Office 文件解析为结构化知识存入记忆底座
2. **配合 embedding 和 chunking**: MinerU 输出的结构化 Markdown/JSON 可天然对接分块策略
3. **灵活部署**: 对于不需要 GPU 的场景，pipeline 后端可在 4GB 显存甚至纯 CPU 上运行
4. **精度分级**: 快速场景用 pipeline (86分)、复杂文档用 hybrid (95分) 的弹性策略
5. **Provider 化包装**: 遵循 perception-agent 的 BasePerceptor 契约封装

### 注意点

- MinerU 规模较大（模型 ~20GB），不适合嵌入式场景
- pipeline 后端虽支持纯 CPU，但需要较多内存 (16GB+)
- 许可证为 MinerU Open Source License（Apache 2.0 衍生），需关注商用合规
- 目前版本 (3.4.3) 已完全移除 AGPLv3 和 CC-BY-NC-SA 模型依赖

---

## 8. 竞品对比

| 能力 | MinerU | Marker | Docling | PyMuPDF4LLM | Azure OCR |
|------|--------|--------|---------|-------------|-----------|
| 开源性 | ✅ 开源 | ✅ 开源 | ✅ 开源 | ✅ 开源 | ❌ 商用 |
| VLM 引擎 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 纯 CPU 支持 | ✅ | ✅ | ✅ | ✅ | — |
| 文档格式 | PDF/DOCX/PPTX/XLSX | PDF | PDF/DOCX/PPTX/XLSX | PDF | PDF/Image |
| 109语言OCR | ✅ | ❌ | ✅ | ❌ | ✅ |
| 表格还原 | HTML/LaTeX | Markdown | HTML | Markdown | HTML |
| 公式 LaTeX | ✅ | ❌ | ❌ | ❌ | ❌ |
| 国产算力 | ✅ 10+ | ❌ | ❌ | ❌ | ❌ |
| 精度 (OmniDocBench) | **86~95** | — | — | — | — |

---

## 9. 参考文献

```bibtex
@article{wang2026mineru2,
  title={MinerU2.5-Pro: Pushing the Limits of Data-Centric Document Parsing at Scale},
  author={Wang, Bin and He, Tianyao and Ouyang, Linke and Wu, Fan and Zhao, Zhiyuan and Chu, Tao and Qu, Yuan and Jin, Zhenjiang and Zeng, Weijun and Miao, Ziyang and others},
  journal={arXiv preprint arXiv:2604.04771},
  year={2026}
}

@article{niu2025mineru2,
  title={Mineru2.5: A decoupled vision-language model for efficient high-resolution document parsing},
  author={Niu, Junbo and Liu, Zheng and Gu, Zhuangcheng and Wang, Bin and Ouyang, Linke and Zhao, Zhiyuan and Chu, Tao and He, Tianyao and Wu, Fan and Zhang, Qintong and others},
  journal={arXiv preprint arXiv:2509.22186},
  year={2025}
}

@article{wang2024mineru,
  title={Mineru: An open-source solution for precise document content extraction},
  author={Wang, Bin and Xu, Chao and Zhao, Xiaomeng and Ouyang, Linke and Wu, Fan and Zhao, Zhiyuan and Xu, Rui and Liu, Kaiwen and Qu, Yuan and Shang, Fukai and others},
  journal={arXiv preprint arXiv:2409.18839},
  year={2024}
}
```

---

> **调研人**: Sisyphus (JanusAgent)
> **最后更新**: 2026-07-09
> **目录**: `docs/survey/perception/MinerU.md`
