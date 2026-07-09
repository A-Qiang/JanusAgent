# 基于 ms-swift 微调 MinerU2.5-1.2B 的学习计划

> 目标：掌握使用 ms-swift 框架对 MinerU2.5 系列多模态文档解析模型进行微调的全流程，
> 最终能够定制训练特定领域的文档解析模型。

---

## 一、基础认知阶段（Day 1-3）

### 1.1 MinerU2.5 模型架构理解

#### 需要掌握的要点：

| 模块 | 说明 |
|------|------|
| **基座架构** | Qwen2-VL (`Qwen2VLForConditionalGeneration`)，1.2B 参数 |
| **视觉编码** | ViT (Vision Transformer)，patch_size=14，32层 depth，1280 embed_dim |
| **语言模型** | 24 层 Transformer decoder，14 个注意力头，896 hidden_size，GQA (2 KV heads) |
| **特殊机制** | MRoPE (多维旋转位置编码)、滑动窗口注意力和全注意力混合 |
| **双阶段推理** | ① 全局版面分析 (Layout Detection) → ② 局部内容识别 (Content Recognition) |
| **特殊 Token** | `<\|vision_start\|>`、`<\|image_pad\|>`、`<\|vision_end\|>`，以及版面框标记 token |

#### 阅读资料：
- [MinerU2.5 论文](https://arxiv.org/abs/2509.22186) — 理解数据引擎和两阶段策略
- [MinerU2.5-Pro 论文](https://arxiv.org/abs/2604.04771) — 理解数据工程驱动的提升路径
- 本地模型配置：`/home/zengqiang/models/MinerU2.5-Pro-2605-1.2B/config.json`
- Qwen2-VL 官方文档

#### 动手练习：
1. 用 `test_mineru_model.py --info` 查看模型配置
2. 用 `test_mineru_model.py --dry-run` 加载模型检查架构
3. 分别用 raw transformers 和 mineru-vl-utils 跑一次推理，理解输出格式

---

### 1.2 ms-swift 框架入门

#### 需要掌握的要点：

| 模块 | 说明 |
|------|------|
| **命令行工具** | `swift sft`、`swift infer`、`swift deploy`、`swift export`、`swift web-ui` |
| **模型注册系统** | `ModelMeta` + `ModelGroup` + `register_model()` 机制 |
| **训练器** | `Seq2SeqTrainer`、RLHF 训练器族 |
| **微调方法** | LoRA、QLoRA、DoRA、LoRA+、全参数微调 |
| **数据集系统** | 内置 150+ 数据集 + 自定义数据集 |
| **模板系统** | chat template 处理多轮对话和多模态输入 |

#### 阅读资料：
- ms-swift README — 概览所有功能
- `swift/model/model_meta.py` — 模型注册的数据结构
- `swift/model/register.py` — 模型加载流程

#### 关键发现：
MinerU2.5-Pro-2604 已在 ms-swift v4.5 中注册（`swift/model/models/qwen.py` 第 816 行）：
```python
ModelGroup([Model('OpenDataLab/MinerU2.5-Pro-2604-1.2B',
                  'opendatalab/MinerU2.5-Pro-2604-1.2B')],
           TemplateType.qwen2_vl),
```
说明它复用了 `Qwen2VLLoader` 和 `TemplateType.qwen2_vl` 模板。

#### 动手练习：
1. 安装 ms-swift：`pip install ms-swift -U`
2. 确认 MinerU2.5 注册：`python -c "from swift.model import MODEL_MAPPING; print('qwen2_vl' in MODEL_MAPPING)"`
3. 跑通 Qwen2-VL 的 SFT 示例：`bash examples/train/multimodal/ocr.sh`
4. 探索 Web-UI：`SWIFT_UI_LANG=en swift web-ui`

---

## 二、环境搭建阶段（Day 4-5）

### 2.1 软硬件环境

#### 推荐配置：

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **GPU** | 1× RTX 3090 (24GB) | 4× RTX 3090 / A100 |
| **Python** | 3.12 | 3.12 |
| **CUDA** | 12.1+ | 12.8 / 13.0 |
| **显存 (LoRA)** | ~9-12 GB | 12-16 GB |
| **显存 (全参)** | ~24 GB | 24+ GB (需 DeepSpeed ZeRO3) |

#### 依赖安装：

```bash
# 基础安装
pip install ms-swift -U

# 如使用 uv（推荐）
uv pip install ms-swift -U --torch-backend=auto

# 验证 MinerU2.5 模型是否可通过 --model 直接传入本地路径
CUDA_VISIBLE_DEVICES=0 swift infer \
    --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B \
    --stream true
```

### 2.2 项目目录规划

```
packages/perception-agent/
├── docs/
│   └── plan/
│       └── README.md           ← 本计划文档
├── finetune/                    # (新建) 微调实验目录
│   ├── configs/                 # 训练配置文件
│   ├── data/                    # 训练数据
│   ├── scripts/                 # 训练脚本
│   └── experiments/             # 实验结果与日志
├── MinerU/                      # MinerU 官方仓库（已有的）
└── test_mineru_model.py         # 现有测试脚本
```

---

## 三、数据准备阶段（Day 6-10）

### 3.1 MinerU2.5 数据格式理解

MinerU2.5 采用两阶段训练数据：

#### 第一阶段：版面分析数据
```
输入: 下采样后的整页图片
输出: 版面元素检测结果（包含边界框和类型标签）

格式:
<|box_start|>x1,y1,x2,y2<|box_end|><|ref_start|>类别<|ref_end|>
类别包括: text, title, table, formula, figure, chart, header, footer, ...
```

#### 第二阶段：内容识别数据
```
输入: 根据第一阶段裁剪的局部区域 + 任务提示
输出: 具体内容的 Markdown/HTML

任务提示:
- "Text Recognition:" → 输出纯文本
- "Table Recognition:" → 输出 HTML/OTSL 表格
- "Formula Recognition:" → 输出 LaTeX 公式
- "Image Analysis:" → 输出图片描述
```

### 3.2 ms-swift 数据集兼容

ms-swift 的自定义数据集要求（以多模态 SFT 为例）每行为一个 JSON 对象：

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "image": "/path/to/page.png"},
        {"type": "text", "text": "Layout Detection:"}
      ]
    },
    {
      "role": "assistant",
      "content": "<|box_start|>10,20,100,200<|box_end|><|ref_start|>text<|ref_end|>..."
    }
  ]
}
```

对于 MinerU 的两阶段数据，有两种思路：

| 方案 | 说明 | 复杂度 |
|------|------|--------|
| **方案 A：端到端** | 合并两个阶段为一个 SFT 训练，输入整图→输出完整 Markdown | ⭐ |
| **方案 B：两阶段分离** | 分别训练版面分析模型和内容识别模型 | ⭐⭐⭐ |
| **方案 C：统一阶段** | 使用类似 MinerU 官方的 prompt-based 方式，把阶段选择作为系统 prompt | ⭐⭐ |

**推荐：先尝试方案 A**，利用 MinerU2.5 已有能力进行领域适应。

### 3.3 数据收集建议

根据不同场景需求：

| 应用场景 | 数据来源 | 标注要求 |
|---------|---------|---------|
| **通用文档增强** | PDF 论文、书籍扫描件 | 需版面标注 + 文本标注 |
| **票据解析** | 发票、收据、合同 | 需字段级标注 |
| **学术论文** | PDF 格式论文 | 需公式/表格精细标注 |
| **手写文档** | 手写笔记、表单 | 需手写内容转写 |

#### 数据增强技巧：
- PDF 渲染 → 不同分辨率的页面图片
- 混入噪声 (模糊、倾斜、光照变化) → 提高鲁棒性
- 合成数据 (程序生成表格/公式) → 扩大覆盖范围
- 参考 MinerU2.5-Pro 的数据工程方法论

### 3.4 数据集注册方法

ms-swift 中两种注册自定义数据集的方式：

**方式 1：直接传路径**
```bash
--dataset '/path/to/my_data.jsonl' \
--custom_dataset_info '{"/path/to/my_data.jsonl": {"columns": {"messages": "messages"}}}'
```

**方式 2：注册数据集类**（参考 `swift/dataset/` 目录下的实现）
```python
# 创建一个数据集注册类
@register_dataset(...)
class MyDocumentDataset(Dataset):
    ...
```

---

## 四、训练配置调优阶段（Day 11-16）

### 4.1 LoRA 微调 (推荐起步)

MinerU2.5-1.2B 使用 Qwen2-VL 架构，其 LoRA 配置如下：

#### 基础模板（参考 ms-swift 已有的 OCR 示例）：

```bash
CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
swift sft \
    --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B \
    --dataset '/path/to/document_data.jsonl' \
    --tuner_type lora \
    --torch_dtype bfloat16 \
    --num_train_epochs 3 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --learning_rate 1e-4 \
    --lora_rank 8 \
    --lora_alpha 32 \
    --target_modules all-linear \
    --freeze_vit true \
    --freeze_aligner true \
    --gradient_accumulation_steps 16 \
    --max_length 4096 \
    --output_dir output/mineru-document-sft \
    --warmup_ratio 0.05 \
    --save_steps 100 \
    --eval_steps 100
```

#### 超参数调节指南：

| 参数 | 建议范围 | 说明 |
|------|---------|------|
| `--lora_rank` | 8-64 | 越大模型容量越大，但显存占用更高 |
| `--lora_alpha` | 16-64 | 通常为 lora_rank 的 2-4 倍 |
| `--learning_rate` | 1e-5 ~ 2e-4 | ViT/LM head 用 1e-5，LLM 用 1e-4 |
| `--target_modules` | all-linear / qkv / specific | "all-linear" 效果最好 |
| `--freeze_vit` | true / false | true：冻结视觉编码器，节省显存 |
| `--max_pixels` | 1003520 (~1008×1008) | 控制输入图片的分辨率上限 |
| `--max_length` | 2048-8192 | 影响显存和可处理的上下文长度 |

### 4.2 价值层冻结策略

MinerU2.5 基于 Qwen2-VL 架构，有三个主要部分可以单独控制：

```bash
# 策略 1：仅训练 LLM 的 LoRA adapter（最省资源）
--freeze_vit true --freeze_aligner true

# 策略 2：同时训练 ViT 和 LLM 的 LoRA
--freeze_vit false --freeze_aligner false
--tuner_type lora

# 策略 3：ViT 全参数 + LLM LoRA（混合训练）
--tuner_type lora_llm
--freeze_vit false
--vit_lr 1e-5 --aligner_lr 1e-5
```

### 4.3 GRPO 强化学习微调（进阶）

MinerU2.5-Pro 论文中提到 GRPO Format Alignment 作为第三阶段训练。

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 \
swift rlhf \
    --rlhf_type grpo \
    --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B \
    --dataset '/path/to/document_data.jsonl' \
    --reward_funcs format
```

需要定义针对文档解析的奖励函数：版面检测准确性、OCR 准确率、表格结构完整性等。

### 4.4 分布式训练

| 方案 | 适用场景 | 配置 |
|------|---------|------|
| **DDP** | 单机多卡 | `NPROC_PER_NODE=4 swift sft ...` |
| **DeepSpeed ZeRO2** | 4卡训练 | `--deepspeed zero2` |
| **DeepSpeed ZeRO3** | 大模型/大batch | `--deepspeed zero3` |
| **FSDP** | 多机训练 | `--fsdp true` |

---

## 五、实验跟踪与评估阶段（Day 17-19）

### 5.1 实验管理

```bash
# 添加 wandb 或 tensorboard 监控
--report_to wandb \

# 定期保存
--save_steps 100 \

# checkpoint 数量限制
--save_total_limit 3
```

### 5.2 评估方法

#### 离线评估：
```bash
CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
swift infer \
    --adapters output/mineru-document-sft/checkpoint-xxx \
    --merge_lora true \
    --infer_backend vllm \
    --stream true
```

#### 使用 mineru-vl-utils 评估：
```python
from mineru_vl_utils import MinerUClient
from mineru_vl_utils.post_process import calculate_metric

client = MinerUClient(
    backend="transformers",
    model="/path/to/merged_model",
    processor="/path/to/merged_model"
)
result = client.two_step_extract(page_image)
# 计算编辑距离、TEDS、CDM 等指标
```

### 5.3 关键指标

| 指标 | 用途 | MinerU2.5-Pro 基线 |
|------|------|-------------------|
| **Text Edit Distance ↓** | 文本识别精度 | 0.036 (OmniDocBench) |
| **Formula CDM ↑** | 公式识别精度 | 97.15 |
| **Table TEDS ↑** | 表格结构精度 | 93.62 |
| **Table TEDS-S ↑** | 表格结构+文本精度 | 96.01 |
| **Read Order Edit ↓** | 阅读顺序准确性 | 0.123 |
| **版面检测 mAP** | 版面元素定位 | — |

---

## 六、部署上线阶段（Day 20-21）

### 6.1 模型导出

```bash
# 合并 LoRA 权重
swift export \
    --adapters output/mineru-document-sft/checkpoint-xxx \
    --merge_lora true \
    --output_dir ./mineru-finetuned

# 推送到 HuggingFace
swift export \
    --adapters output/mineru-document-sft/checkpoint-xxx \
    --merge_lora true \
    --push_to_hub true \
    --hub_model_id your-username/mineru-finetuned \
    --use_hf true
```

### 6.2 推理部署

```bash
# vLLM 部署
swift deploy \
    --model /path/to/merged_model \
    --infer_backend vllm

# 调用 API
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "mineru-finetuned",
        "messages": [
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
                {"type": "text", "text": "Layout Detection:"}
            ]}
        ]
    }'
```

### 6.3 集成到 perception-agent

将微调后的 MinerU 模型接入 JanusAgent 感知层：

```python
# perception-agent/src/perceivers/document.py
from mineru_vl_utils import MinerUClient

class MinerUDocumentPerceiver(BasePerceptor):
    def __init__(self, model_path: str):
        self.client = MinerUClient(
            backend="transformers",
            model_name_or_path=model_path,
        )

    def perceive(self, image: Image.Image) -> str:
        result = self.client.two_step_extract(image)
        from mineru_vl_utils.post_process import json2md
        return json2md(result)
```

---

## 七、项目实施路线图

```
Week 1: 基础与环境
  ├─ Day 1: 阅读 MinerU2.5 论文 + 理解模型架构
  ├─ Day 2: 跑通 MinerU 推理流程 (transformers + mineru-vl-utils)
  ├─ Day 3: 安装 ms-swift + 跑通 Qwen2-VL 训练示例
  ├─ Day 4: 搭建开发环境 (CUDA, 依赖, 目录结构)
  └─ Day 5: 注册自定义模型/确认 MinerU 模型兼容性

Week 2: 数据处理
  ├─ Day 6-7: 收集第一版训练数据 (公开文档数据集或自采)
  ├─ Day 8: 整理数据格式 (JSONL, ms-swift 兼容)
  ├─ Day 9: 数据清洗与质量检验
  └─ Day 10: 编写数据加载器/注册自定义数据集

Week 3: 训练与调优
  ├─ Day 11: 第一版 LoRA 微调 (小批量，快速验证)
  ├─ Day 12: 超参数调优 (lr, lora_rank, freeze 策略)
  ├─ Day 13: 冻结策略对比实验 (ViT 冻结 vs 不冻结)
  ├─ Day 14: 多卡训练 + DeepSpeed 配置
  ├─ Day 15: GRPO 强化学习微调尝试
  └─ Day 16: 多次实验对比，找到最佳配置

Week 4: 评估与部署
  ├─ Day 17: 定量评估 (Text ED, TEDS, CDM 等指标)
  ├─ Day 18: 定性评估 (人工检查版面分析和内容提取结果)
  ├─ Day 19: 多轮迭代改进 (Bad Case 分析 → 补充数据 → 重训)
  ├─ Day 20: 模型导出 + vLLM 部署
  └─ Day 21: 对接 JanusAgent perception-agent 管线
```

---

## 八、常见问题与故障排除

### 8.1 OOM (显存不足)

```bash
# 解决方案
--per_device_train_batch_size 1
--gradient_accumulation_steps 32   # 增大来弥补 bs=1 的影响
--max_length 2048                   # 减小最大长度
--freeze_vit true
--disable_flash_attn false
# 或切换到 DeepSpeed ZeRO3
--deepspeed zero3
```

### 8.2 MinerU 在 ms-swift 中的特殊性

由于 MinerU 使用了特殊的 chat template 和两阶段推理流程：

1. **推理时**需要用 mineru-vl-utils 进行两阶段处理和结果后处理
2. **训练时**可以直接复用 Qwen2-VL 的标准 SFT/RLHF 流程
3. **数据组织**需要确保训练数据包含正确的特殊 token 序列

### 8.3 其他注意事项

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 训练 loss 不下降 | lr 太小或数据问题 | 调大 lr，检查数据标注质量 |
| 推理输出乱码 | 模板不匹配 | 检查 chat template 是否正确传递 |
| 微调后版面分析变差 | 灾难性遗忘 | 减少学习率，加入经验回放 |
| 图片无法加载 | 像素超过限制 | 设置 `MAX_PIXELS` 环境变量 |

---

## 九、参考资料

### 论文
- [MinerU2.5: A Decoupled VLM for Document Parsing](https://arxiv.org/abs/2509.22186)
- [MinerU2.5-Pro: Data-Centric Document Parsing](https://arxiv.org/abs/2604.04771)
- [ms-swift Paper (AAAI 2025)](https://arxiv.org/abs/2408.05517)

### 代码仓库
- [ms-swift](https://github.com/modelscope/ms-swift) — 训练框架
- [MinerU](https://github.com/opendatalab/MinerU) — 文档解析工具
- [mineru-vl-utils](https://github.com/opendatalab/mineru-vl-utils) — MinerU VLM 工具库

### 模型
- [MinerU2.5-2509-1.2B (HF)](https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B)
- [MinerU2.5-Pro-2604-1.2B (HF)](https://huggingface.co/opendatalab/MinerU2.5-Pro-2604-1.2B)
- [MinerU2.5-Pro-2605-1.2B (本地)](file:///home/zengqiang/models/MinerU2.5-Pro-2605-1.2B)

### 文档
- [ms-swift 官方文档](https://swift.readthedocs.io/en/latest/)
- [ms-swift 多模态训练指南](https://swift.readthedocs.io/en/latest/Instruction/LLM/VLLMBestPractices.html)

---

*最后更新: 2026-07-09*
*计划版本: v1.0*
