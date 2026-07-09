# ms-swift 框架入门参考文档

> 面向 MinerU2.5 微调的实践指南，从一个命令开始，逐步深入框架内核。
> 本文搭配 `packages/perception-agent/finetune/` 目录使用。

---

## 目录

1. [ms-swift 是什么](#1-ms-swift-是什么)
2. [快速安装与环境验证](#2-快速安装与环境验证)
3. [CLI 五虎将：五分钟速览全部命令](#3-cli-五虎将五分钟速览全部命令)
4. [第一个 SFT：跑通 ocr.sh](#4-第一个-sft跑通-ocrsh)
5. [改造成 MinerU2.5 专属训练脚本](#5-改造成-mineru25-专属训练脚本)
6. [训练参数详解字典](#6-训练参数详解字典)
7. [模型注册系统剖析](#7-模型注册系统剖析)
8. [Web-UI 交互式训练](#8-web-ui-交互式训练)
9. [自定义数据集接入](#9-自定义数据集接入)
10. [推理与评估工作流](#10-推理与评估工作流)
11. [常见问题排查清单](#11-常见问题排查清单)

---

## 1. ms-swift 是什么

**ms-swift** = ModelScope SWIFT 是阿里巴巴开源的 **全栈大模型训练与部署框架**（AAAI 2025），核心特性：

```
一句话概括：你给模型和数据，它负责剩下的训练、评估、部署全流程。
```

### 能力矩阵

| 维度 | 能力 |
|------|------|
| **模型范围** | 600+ 文本模型 + 400+ 多模态模型 |
| **训练算法** | SFT / PT / DPO / GRPO / KTO / RM / PPO ... |
| **微调方法** | LoRA / QLoRA / DoRA / LoRA+ / GaLore / LISA / UnSloth / 全参 FT |
| **分布式** | DDP / DeepSpeed ZeRO-2/3 / FSDP / Megatron |
| **推理后端** | transformers / vLLM / SGLang / LMDeploy |
| **开放注册** | 任何人都可以注册新的模型和数据集 |

### 关于 MinerU2.5 的一个重要事实

**MinerU2.5-Pro-2604（不是 2605）已经直接在 ms-swift 中注册**，作为 `qwen2_vl` 分类下的一个成员：

```
MLLMModelType.qwen2_vl 包含 ↓
  ├── Qwen/Qwen2-VL-2B/7B/72B（instruct + base）
  ├── Bytedance UI-TARS-2B/7B/72B
  ├── allenai/olmOCR-7B
  ├── OpenDataLab/MinerU2.5-Pro-2604-1.2B   ← 在这里
  └── Qwen/QVQ-72B-Preview
```

这意味着你的 **本地 2605 版本**（相同架构 Qwen2VLForConditionalGeneration）不需任何额外注册，直接用 `--model /path/to/local` 就能训练。

---

## 2. 快速安装与环境验证

### 2.1 安装

```bash
# 方式一：pip 安装（推荐，最新发布版）
pip install ms-swift -U

# 方式二：uv 安装（如果装了 uv，更快）
uv pip install ms-swift -U --torch-backend=auto

# 方式三：源码安装（如果你想修改源码）
git clone https://github.com/modelscope/ms-swift.git
cd ms-swift && pip install -e .
```

### 2.2 最小验证

```bash
# 验证1：能看到帮助文档
swift --help

# 验证2：确认 MinerU 依赖的 qwen2_vl model_type 已注册
python -c "
from swift.model import MODEL_MAPPING
print('qwen2_vl' in MODEL_MAPPING)  # 应输出 True
print(len(MODEL_MAPPING))           # 应输出 250+
"

# 验证3：能加载 MinerU2.5 本地模型做推理
CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
swift infer \
    --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B \
    --stream true
```

如果验证3报错 `<model_type> auto`，需要在参数里加 `--model_type qwen2_vl` 或者 `--template_type qwen2_vl` 手动指定。

### 2.3 为什么有时要手动指定 model_type？

ms-swift 自动检测模型类型的逻辑是：

```
用户输入 --model path_or_name
        ↓
  1. 读取 config.json 的 architectures 字段
        ↓
  2. 遍历 MODEL_MAPPING，看哪个 model_type 声明的 architectures 配得上
        ↓
  3. 如果配不上，fallback 到名字相似度匹配
        ↓
  4. 还不行 → 报错，让你手工指定
```

如果你的本地模型 `config.json` 中有 `"architectures": ["Qwen2VLForConditionalGeneration"]`，那自动检测就能命中 `qwen2_vl`。否则就加：

```bash
--model_type qwen2_vl
```

---

## 3. CLI 五虎将：五分钟速览全部命令

ms-swift 提供 6 个核心 CLI 子命令，覆盖训练到部署全链路：

```
swift
├── sft        ← 监督微调（你用得最多的）
├── rlhf       ← 强化学习训练（GRPO/DPO/PPO/KTO）
├── infer      ← 交互式或批量推理
├── deploy     ← 启动 vLLM/SGLang 推理服务
├── export     ← 模型导出（合并 LoRA、Push Hub）
└── web-ui     ← 图形界面操作（新手友好）
```

### 3.1 `swift sft` — 核心训练入口

```bash
swift sft \
    --model Qwen/Qwen2.5-VL-7B-Instruct \
    --dataset 'AI-ModelScope/LaTeX_OCR:human_handwrite#20000' \
    --tuner_type lora \
    --output_dir output
```

子命令 | 对应源文件 | 一句话说明
---|---|---
`sft` | `swift/cli/sft.py` | 有监督微调 — 对标 `transformers.Trainer` 的多模态增强版
`rlhf` | `swift/cli/rlhf.py` | 强化学习 — GRPO / DPO / PPO / KTO 等
`infer` | `swift/cli/infer.py` | 推理 — 交互式/批量/数据集评估
`deploy` | `swift/cli/deploy.py` | 部署 — 启动 OpenAI 兼容 API 服务器
`export` | `swift/cli/export.py` | 导出 — 合并 LoRA / 转换格式 / Push Hub
`web-ui` | `swift/cli/web_ui.py` | 网页 UI — 可视化操作面板

### 3.2 各命令速查

```bash
# sft: 训练完成后自动保存到 --output_dir
swift sft --model xxx --dataset xxx ...

# infer: 加载训练好的 checkpoint 交互问答
swift infer --adapters output/vx-xxx/checkpoint-xxx --stream true

# deploy: 启动兼容 OpenAI API 的服务
swift deploy --model /path/to/model --infer_backend vllm
# 然后就可以 curl 访问 http://localhost:8000/v1/chat/completions

# export: 合并 LoRA → 完整权重
swift export --adapters output/vx-xxx/checkpoint-xxx --merge_lora true --output_dir merged_model

# web-ui: 浏览器打开，点击配置即可
SWIFT_UI_LANG=en swift web-ui
```

---

## 4. 第一个 SFT：跑通 ocr.sh

这是 ms-swift 自带的一个多模态 LoRA 训练示例，是你学习的最佳起点。

### 4.1 脚本原文

```bash
#!/bin/bash
# 20GB 显存需求
CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
swift sft \
    --model Qwen/Qwen2.5-VL-7B-Instruct \
    --dataset 'AI-ModelScope/LaTeX_OCR:human_handwrite#20000' \
    --load_from_cache_file true \
    --split_dataset_ratio 0.01 \
    --tuner_type lora \
    --torch_dtype bfloat16 \
    --num_train_epochs 1 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --learning_rate 1e-4 \
    --lora_rank 8 \
    --lora_alpha 32 \
    --target_modules all-linear \
    --freeze_vit true \
    --freeze_aligner true \
    --gradient_accumulation_steps 16 \
    --eval_steps 50 \
    --save_steps 50 \
    --save_total_limit 2 \
    --logging_steps 5 \
    --max_length 4096 \
    --output_dir output \
    --warmup_ratio 0.05 \
    --dataloader_num_workers 4
```

### 4.2 每条参数的用意

从左到右解读这个脚本的信号流：

```
环境变量
├── CUDA_VISIBLE_DEVICES=0      ← 只用 GPU 0
└── MAX_PIXELS=1003520           ← 图片最大像素数（≈1008×1008）
                                   MinerU 文档场景可调大为 2007040

数据集处理
├── --dataset '...LaTeX_OCR:human_handwrite#20000'
│    ↑ 数据集名  ↑ 子集  ↑ 采样 20000条（留空=全部）
├── --load_from_cache_file true ← 用缓存，第二次跑更快
└── --split_dataset_ratio 0.01 ← 只拿 1% 做 eval（数据量大时的节省手段）

微调方式
├── --tuner_type lora           ← LoRA 微调
├── --lora_rank 8               ← LoRA 秩（越大代表越多参数被训练）
├── --lora_alpha 32             ← LoRA 缩放系数（通常 = rank × 2~4）
└── --target_modules all-linear ← 在所有线性层上都挂 LoRA adapter

冻结策略
├── --freeze_vit true           ← 冻结视觉编码器（ViT），省大量显存
└── --freeze_aligner true       ← 冻结视觉-语言连接投影层

训练超参
├── --num_train_epochs 1        ← 遍历一遍数据集
├── --learning_rate 1e-4        ← LoRA 常用学习率（全参一般用 1e-5）
├── --per_device_train_batch_size 1  ← 每张卡每步一个样本
├── --gradient_accumulation_steps 16 ← 累积 16 步更新一次，等效 batch=16
├── --max_length 4096           ← 最长 4096 token（超出截断）
└── --warmup_ratio 0.05         ← 前 5% step 线性预热学习率

技术选型
├── --torch_dtype bfloat16      ← BF16 精度（比 FP16 更稳定）
└── --dataloader_num_workers 4  ← 4 个子进程加载数据

日志与保存
├── --eval_steps 50             ← 每 50 步 eval 一次
├── --save_steps 50             ← 每 50 步保存 checkpoint
├── --save_total_limit 2        ← 只保留最近 2 个 checkpoint
├── --logging_steps 5           ← 每 5 步打印 loss
└── --output_dir output         ← 所有产物放这里
```

### 4.3 先做一次小规模试跑

```bash
# 复制到 finetune 目录
cp /tmp/ms-swift/examples/train/multimodal/ocr.sh \
   packages/perception-agent/finetune/scripts/

# 改成能迅速出结果的小配置（强制只有 1 条样本的 eval）
cd packages/perception-agent/finetune

CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
swift sft \
    --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B \
    --dataset 'AI-ModelScope/LaTeX_OCR:human_handwrite#200' \
    --split_dataset_ratio 0.5 \
    --tuner_type lora \
    --torch_dtype bfloat16 \
    --num_train_epochs 1 \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 4 \
    --freeze_vit true \
    --freeze_aligner true \
    --lora_rank 8 \
    --target_modules all-linear \
    --learning_rate 1e-4 \
    --max_length 4096 \
    --output_dir output/test-run \
    --logging_steps 1 \
    --eval_steps 5 \
    --save_steps 10 \
    --save_total_limit 1
```

这次试跑的预期产出：

```
output/test-run/
├── checkpoint-10/        ← 第一个 checkpoint
├── checkpoint-20/        ← 第二个 checkpoint
├── logging.jsonl         ← 完整的 loss 日志
├── args.json             ← 本次训练的完整参数存档
└── vx-xxx/ ↔            ← wandb/tensorboard 日志（如果有配置）

终端输出示例：
{ "loss": 3.8412, "acc": 3.091, "lr": 1e-4, "step": 1 }
{ "loss": 2.5412, "acc": 4.053, "lr": 1e-4, "step": 2 }
...
{ "eval_loss": 2.553, "eval_acc": 3.894, "epoch": 0.04 }
```

> **要点**：你需要观察的是 loss 是否持续下降。不一定降到 0，只要趋势向下就是正常的。

---

## 5. 改造成 MinerU2.5 专属训练脚本

基于 ocr.sh 改造，几处关键改动：

```bash
#!/bin/bash
# MinerU2.5-Pro-2605 LoRA SFT 首次训练脚本
# 保存到: finetune/scripts/sft_first_run.sh

CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
swift sft \
    --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B \
    --model_type qwen2_vl \               # ← 新增：防止自动检测失败
    --template_type qwen2_vl \             # ← 新增：明确指定模板
    --dataset '/path/to/your/data.jsonl' \ # ← 改为自己的数据
    --tuner_type lora \
    --torch_dtype bfloat16 \
    --num_train_epochs 3 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --learning_rate 1e-4 \
    --lora_rank 8 \
    --lora_alpha 32 \
    --target_modules all-linear \
    --freeze_vit true \
    --freeze_aligner true \
    --max_length 4096 \
    --output_dir output/mineru-first-run \
    --warmup_ratio 0.05 \
    --logging_steps 5 \
    --eval_steps 100 \
    --save_steps 100 \
    --save_total_limit 3 \
    --dataloader_num_workers 4 \
    --report_to tensorboard \              # ← 新增：开启可视化的训练监控
    --split_dataset_ratio 0.1              # ← 取 10% 作验证集
```

### 相比 ocr.sh 的主要变化

| 项目 | ocr.sh | MinerU 脚本 | 为什么改 |
|------|--------|-------------|----------|
| `--model` | Qwen2.5-VL-7B | 本地 MinerU 路径 | 当然要换成自己的模型 |
| `--model_type`| 缺省 | 显式设置 | 避免本地路径 + 非标准名称导致自动检测失败 |
| `--template_type` | 缺省 | 显式设置 | Chrome 保险 |
| `--num_train_epochs` | 1 | 3 | 小模型 3 epoch 才能充分学习 |
| `--report_to` | 缺省 | tensorboard | 可视化 loss 曲线更方便调试 |

---

## 6. 训练参数详解字典

把所有参数按功能分类。这里是不需要翻文档的快速查询表。

### 6.1 模型加载参数

| 参数 | 示例值 | 含义 |
|------|--------|------|
| `--model` | `Qwen/Qwen2-VL-7B` | 模型名称（HF 官网名）或本地路径 |
| `--model_type` | `qwen2_vl` | 直接指定 model_type，跳过自动检测 |
| `--template_type` | `qwen2_vl` | 直接指定聊天模板 |
| `--torch_dtype` | `bfloat16` / `float16` / `float32` | 加载精度 |
| `--quant_bits` | `4` / `8` | 量化位数（配合 QLoRA） |

### 6.2 微调方式参数

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--tuner_type` | `lora` / `full` / `lora_llm` / `qlora` ... | 微调方法 |
| `--lora_rank` | 4 ~ 128 | LoRA 秩，越大能力越强但也越贵 |
| `--lora_alpha` | 8 ~ 256 | LoRA 缩放因子，通常 rank × 2 |
| `--target_modules` | `all-linear` / `qkv` / `["q_proj","v_proj"]` | 哪些模块挂 LoRA |

**三种 tuner_type 的选择指南：**

```bash
--tuner_type lora        # 【默认】只在部分层加 adapter，最快最省显存
                          # 适合 1 卡场景、起步验证

--tuner_type lora_llm    # LLM 部分用 LoRA，ViT/Aligner 全参数训练
                          # 适合需要加强视觉理解的场景

--tuner_type full        # 全参数训练，需要多卡和 DeepSpeed
                          # 效果最好也最贵，丹药级投入
```

### 6.3 冻结策略参数

```
--freeze_vit true       视觉编码器不动（省 40% 显存，起步推荐）
--freeze_aligner true   视觉连接投影层不动（省 5%，常跟 freeze_vit 一起）
--freeze_llm false      语言模型（训练的绝对主力，不建议冻结）
```

传给底层 `MultiModelKeys` 的控制信号：

```
freeze_vit=true    → language_model 参数更新，vision_tower 冻结
freeze_llm=true    → vision_tower 参数更新，language_model 冻结
freeze_aligner=true→ aligner 对应的层冻结
```

### 6.4 数据参数

| 参数 | 说明 |
|------|------|
| `--dataset` | 数据集。支持多种格式：HF 数据集名、本地 JSONL 路径 |
| `--dataset` 特殊语法 | `dataset:subset#N` = 取 subset 子集的 N 条 |
| `--split_dataset_ratio` | 切分比例，`0.1` = 10% 做验证集，90% 做训练集 |
| `--max_length` | 最大 token 数，超过截断。设太大会 OOM |
| `--custom_dataset_info` | 自定义数据集的列映射配置 |

### 6.5 训练超参

| 参数 | 典型值 | 说明 |
|------|--------|------|
| `--num_train_epochs` | 3 | 训练轮数 |
| `--per_device_train_batch_size` | 1〜4 | 每设备 batch size |
| `--gradient_accumulation_steps` | 8〜32 | 梯度累积步数，等效 batch = per_device × accum × num_gpu |
| `--learning_rate` | 1e-4(LoRA) / 1e-5(full) | 学习率 |
| `--weight_decay` | 0.01 | 权重衰减，防过拟合 |
| `--warmup_ratio` | 0.05 | 学习率预热步数占比 |
| `--lr_scheduler_type` | cosine | 学习率调度策略 |

### 6.6 图片处理参数

| 参数/环境变量 | 说明 |
|--------------|------|
| `MAX_PIXELS` (环境变量) | 单张图片最大像素数。常见值：`1003520` (~1008²), `2007040` (~1400²) |
| `MIN_PIXELS` (环境变量) | 单张图片最小像素数。默认 3136 |
| `--max_pixels` | 同上，作为 CLI 参数传入（某些版本支持）|

**调高 `MAX_PIXELS` 可以提高 OCR 精度**，但显存开销也会同步增长。

### 6.7 日志与保存

| 参数 | 说明 |
|------|------|
| `--output_dir` | 所有产物的输出根目录 |
| `--logging_steps` | 每隔多少步打印一次 loss |
| `--save_steps` | 每隔多少步保存 checkpoint |
| `--save_total_limit` | 最多保留多少个旧 checkpoint（自动删除最早的）|
| `--eval_steps` | 每隔多少步在验证集上评估 |
| `--report_to` | 日志上报目标：`tensorboard` / `wandb` / `none` |

---

## 7. 模型注册系统剖析

理解这个系统有助于你判断何时该自行注册一个模型类型。

### 7.1 三层数据结构

```
MODEL_MAPPING (全局字典)
 │
 ├── key: model_type (字符串, 如 "qwen2_vl")
 │
 └── value: ModelMeta (数据类)
       │
       ├── model_type: MLLMModelType.qwen2_vl   ← 唯一 ID
       ├── model_groups: [
       │     ModelGroup(models=[
       │       Model(ms_model_id="Qwen/Qwen2-VL-7B", hf_model_id="Qwen/Qwen2-VL-7B"),
       │       ...
       │     ], template="qwen2_vl")
       │     ModelGroup(models=[
       │       Model(ms_model_id="OpenDataLab/MinerU2.5-Pro..."),  ← MinerU 在这里
       │     ], template="qwen2_vl")
       │   ]
       ├── loader: Qwen2VLLoader.class           ← 怎么加载模型
       ├── model_arch: qwen2_vl                  ← 对应哪个架构注册
       ├── template: "qwen2_vl"                  ← 用什么聊天模板
       ├── architectures: ["Qwen2VLForCondGen"]  ← 匹配 config.json
       ├── requires: ["transformers>=4.45"]      ← 依赖库版本
       └── tags: ["vision", "video"]             ← 搜索标签
```

### 7.2 ModelLoader 的工作流程

```
Qwen2VLLoader.get_model()
  └── Qwen2VLForConditionalGeneration.from_pretrained(model_dir, ...)
      └── 会根据 config.json 中的 architecture 自动选择正确的类

Qwen2VLLoader.get_processor()
  └── AutoProcessor.from_pretrained(model_dir, ...)
      └── 加载 tokenizer + image_processor
```

MinerU2.5 共用的是 `Qwen2VLLoader`，也就是说它的加载流程与 Qwen2-VL 完全一致。

### 7.3 什么是 model_arch？为什么它决定了 freeze_vit 的行为？

```python
# model_arch.py 中的注册
register_model_arch(MultiModelKeys(
    ModelArch.qwen2_vl,
    language_model=['model.language_model', 'lm_head'],  # ← 属于 LLM 的权重前缀
    vision_tower=['model.visual'],                         # ← 属于 ViT 的权重前缀
    aligner=['model.visual.merger'],                       # ← 属于对齐层的权重前缀
))

# 当设置 --freeze_vit true 时，ms-swift 内部会：
# 1. 查 model_arch，找到 vision_tower 的参数前缀 = ['model.visual']
# 2. 在模型中筛出所有以 'model.visual' 开头的参数
# 3. 把这些参数的 requires_grad 设为 False
```

如果未来你想注册一个新的 OCR 模型（不是基于 Qwen2-VL 的），你就需要自己写 `MultiModelKeys` 指明各部件的权重前缀。

### 7.4 什么时候需要自行注册？

| 场景 | 需要注册吗？ |
|------|------------|
| 直接用 MinerU2.5-Pro-2604/2605 训练 | ❌ 不用 — 已是 qwen2_vl 家族 |
| 换了一个新的 Qwen2-VL base 模型微调 | ❌ 不用 — 也属于 qwen2_vl |
| 从头训练一个新架构（类似于 DeepSeek-OCR） | ✅ 需要 — 新建 model_type + ModelLoader |

---

## 8. Web-UI 交互式训练

如果你不想敲命令，ms-swift 提供了图形界面。

```bash
# 启动（英文界面）
SWIFT_UI_LANG=en swift web-ui

# 启动后浏览器打开 http://localhost:7860
```

UI 界面布局：

```
┌───────────── Tab 栏 ──────────────────────┐
│  训练(Train)  │  推理(Infer)  │  模型导出   │
├─────────────────────────────────────────────┤
│                                            │
│  ┌─ 模型配置 ──────────────────────────┐   │
│  │  Model: [/path/to/model]            │   │   ← 填写模型路径
│  │  Model Type: [qwen2_vl ▼]          │   │   ← 下拉选择
│  │  Tuner Type: [lora ▼]              │   │
│  └──────────────────────────────────────┘   │
│  ┌─ 数据集配置 ───────────────────────┐   │
│  │  Dataset: [/path/to/data.jsonl]    │   │   ← 数据集路径
│  │  ...                               │   │
│  └──────────────────────────────────────┘   │
│  ┌─ 训练参数 ─────────────────────────┐   │
│  │  Learning Rate: [1e-4    ]         │   │   ← 数字输入框
│  │  LoRA Rank: [8        ]           │   │
│  │  ...                               │   │
│  └──────────────────────────────────────┘   │
│  [🚀 Start Training]                       │
└─────────────────────────────────────────────┘
```

适合的场景：
- 第一次接触，想可视化理解参数含义
- 快速小规模验证（不用写脚本）
- 展示给团队成员看流程

不适合的场景：
- 大规模实验（还是得脚本 + 后台跑）
- 精细控制多个环境变量

---

## 9. 自定义数据集接入

ms-swift 有两种方式传入自定义数据集。

### 9.1 方式一：直接传 JSONL 路径（推荐起步）

数据格式——每一行是一个完整的对话样本：

```jsonl
{"messages": [
  {"role": "user", "content": [
    {"type": "image", "image": "/absolute/path/to/page_001.png"},
    {"type": "text", "text": "Layout Detection:"}
  ]},
  {"role": "assistant", "content": "<|box_start|>10,20,100,200<|box_end|><|ref_start|>text<|ref_end|><|box_start|>..."}
]}
```

```jsonl
{"messages": [
  {"role": "user", "content": [
    {"type": "image", "image": "https://example.com/page_002.jpg"},
    {"type": "text", "text": "Text Recognition:"}
  ]},
  {"role": "assistant", "content": "This is the recognized text content..."}
]}
```

使用方法：

```bash
swift sft \
    --model /path/to/model \
    --dataset '/path/to/my_data.jsonl' \
    --custom_dataset_info '{
        "/path/to/my_data.jsonl": {
            "columns": {"messages": "messages"}
        }
    }'
```

### 9.2 方式二：编写注册类（大规模/复杂数据管道）

当你需要在线处理图片、多线程预处理、复杂的采样逻辑时，写一个数据集类：

```python
# save as: finetune/data/my_dataset.py
from datasets import Dataset
from swift.dataset import register_dataset

@register_dataset(
    dataset_name='my_document_dataset',
    columns=['messages', 'images', 'objects']
)
def create_document_dataset(dataset_name, *args, **kwargs):
    # 1. 加载原始文件
    # 2. 图片预处理（裁剪、归一化）
    # 3. 组装成 messages 格式
    # 4. 返回 Dataset 对象
    data = []
    for json_line in open('/path/to/raw_data.jsonl'):
        data.append({
            'messages': [...],
            'images': [...],
        })
    return Dataset.from_list(data)
```

### 9.3 如何验证数据格式正确？

先用一条数据跑 `swift infer`：

```bash
# 准备一张测试图片和一条测试消息
echo '{"messages":[{"role":"user","content":[{"type":"image","image":"/tmp/test_page.png"},{"type":"text","text":"Text Recognition:"}]},{"role":"assistant","content":"Expected output"}]}' > /tmp/test_single.jsonl

# 用一条数据验证训练流程通顺
swift sft \
    --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B \
    --dataset /tmp/test_single.jsonl \
    --custom_dataset_info '{"tmp_test_single":{"columns":{"messages":"messages"}}}' \
    --tuner_type lora \
    --num_train_epochs 1 \
    --lora_rank 8 \
    --target_modules all-linear \
    --freeze_vit true \
    --freeze_aligner true \
    --max_length 4096 \
    --output_dir output/verify-data-format \
    --logging_steps 1
```

如果这条能跑通没有报错，说明数据格式是对的。

---

## 10. 推理与评估工作流

### 10.1 用 swift infer 查看训练效果

```bash
# 加载训练好的 checkpoint 做交互式推理
CUDA_VISIBLE_DEVICES=0 \
MAX_PIXELS=1003520 \
swift infer \
    --adapters output/mineru-first-run/checkpoint-300 \
    --model_type qwen2_vl \
    --stream true \
    --load_data_args true
```

这会从 checkpoint 里自动读取模型的路径、模板等信息，然后进入交互式对话模式，你可以随时输入图片路径和文字问它。

### 10.2 Merge LoRA 权重后再推理

```bash
# 先把 LoRA 合并进 base 模型
swift export \
    --adapters output/mineru-first-run/checkpoint-xxx \
    --merge_lora true \
    --output_dir output/mineru-merged

# 然后用完整的模型推理
swift infer \
    --model output/mineru-merged \
    --stream true
```

合并后的模型就是一个标准的 HF 模型目录，也可以被 mineru-vl-utils 加载：

```python
from mineru_vl_utils import MinerUClient
client = MinerUClient(
    backend="transformers",
    model_name_or_path="output/mineru-merged",
)
result = client.two_step_extract(page_image)
```

### 10.3 TensorBoard 监控训练过程

终端 A：启动训练
```bash
bash finetune/scripts/sft_first_run.sh
```

终端 B：打开 TensorBoard
```bash
tensorboard --logdir output/mineru-first-run --port 6006
# 浏览器打开 http://localhost:6006
```

可以看到实时更新的：
- `train/loss` — 训练损失（期望稳步下降）
- `eval/loss` — 验证损失（期望与 train/loss 同趋势）
- `train/learning_rate` — 学习率变化曲线
- `train/grad_norm` — 梯度范数（过大说明不稳定）

### 10.4 完整评估流程

```
训练完成
    │
    ├─ 定量评估
    │   ├─ swift infer + 数据集 → 批量预测
    │   ├─ 计算 Text ED / TEDS / CDM（对比 baseline）
    │   └─ 产出报告图表
    │
    └─ 定性评估
        ├─ 随机抽 50 张测试集图片
        ├─ 肉眼对比 Baseline vs Finetuned
        ├─ 按错误类型分类：文本/表格/公式/版面/阅读顺序
        └─ 选出最难 case → 补充到下一轮训练集
```

---

## 11. 常见问题排查清单

### 11.1 命令行常见报错

| 报错信息 | 根本原因 | 解决方案 |
|----------|---------|---------|
| `ValueError: model_type is not set` | 自动检测失败 | 加 `--model_type qwen2_vl` |
| `KeyError: qwen2_vl not in MODEL_MAPPING` | 安装的版本不对或没装好 | `pip install ms-swift -U` |
| `AttributeError: 'NoneType' has no attribute 'global_vars'` | `qwen_vl_utils` 版本冲突 | `pip install qwen_vl_utils>=0.0.6` |
| `CUDA out of memory` | 显存不够 | 降低 `MAX_PIXELS`、`max_length`、`--freeze_vit true` |
| `ImportError: decord` | 缺少视频处理库 | `pip install decord`（虽然我们是文档不需要，但 qwen2_vl 注册时声明了这个依赖）|
| `FileNotFoundError: ...does not exist` | 路径不对或 HuggingFace 缓存过期 | 检查模型路径或用 `safe_snapshot_download` 重新下载 |
| `RuntimeError: Input image pixels ${x} exceeds limit ${MAX_PIXELS}` | 图片太大 | 设置 `MAX_PIXELS=2007040` 或更高的值 |

### 11.2 数据相关问题

| 现象 | 原因 | 解决 |
|------|------|------|
| Loss 一直 > 5 不下降 | 数据集有问题或 lr 不合适 | 先检查数据格式，再试试 lr=2e-4 |
| Loss 降很快但推理拉胯 | 过拟合或数据量太少 | 增加数据量 / 增大 lora_rank / 加 dropout |
| 推理输出一堆特殊 token 乱码 | template 不匹配 | 确认 `--template_type qwen2_vl` |
| 训练很快但 loss 震荡 | lr 太高 / batch 太小 | 降低 lr 或增大 gradient_accumulation_steps |

### 11.3 性能优化捷径

```bash
# 显存不够怎么办？（从最有效到最次）
1. --per_device_train_batch_size 1           # 减到不能再减
2. --gradient_accumulation_steps 32          # 补 batch size
3. MAX_PIXELS=501760                          # 降低图片分辨率 (= 700×700)
4. --freeze_vit true                          # 冻结 ViT
5. --max_length 2048                          # 缩短序列长度
6. --tuner_type lora --lora_rank 4            # 缩小 LoRA rank
7. --deepspeed zero3                          # ZeRO-3 分片优化器状态

# 训练太慢怎么办？
1. --packing true                              # 样本打包训练（3× 加速）
2. NPROC_PER_NODE=4                            # 4卡并行
3. --deepspeed zero2                           # ZeRO-2
4. --dataloader_num_workers 8                  # 更多加载进程
5. --gradient_checkpointing true               # 梯度检查点
```

---

## 附录：ms-swift 源码地图

```
swift/
├── cli/                    ← CLI 入口（sft.py, infer.py, deploy.py ...）
├── model/                  ← 模型注册系统（核心）
│   ├── constant.py         ← MLLMModelType / LLMModelType 枚举
│   ├── model_meta.py       ← ModelMeta / ModelGroup / Model 数据类 & MODEL_MAPPING
│   ├── model_arch.py       ← MultiModelKeys 架构注册 & MODEL_ARCH_MAPPING
│   ├── register.py         ← register_model(), ModelLoader 基类
│   └── models/             ← 各模型家族的具体注册（qwen.py, deepseek.py ...）
├── dataset/                ← 内置数据集注册
├── trainer/                ← 训练器（Seq2SeqTrainer, RLHF trainers）
├── template/               ← Chat template 系统
└── hparams/                ← 训练参数配置类
```

**新手学习路径**（按推荐顺序）：

```
第1步: cli/sft.py              ← 了解 SFT 训练入口接受的参数
第2步: examples/train/multimodal/ocr.sh  ← 跑起来再说
第3步: model/constant.py       ← 知道有哪些 model_type
第4步: model/model_meta.py     ← 理解模型注册的数据结构
第5步: model/models/qwen.py:775~823  ← 看看 MinerU2.5 是怎么注册的
第6步: model/register.py       ← 知道注册和加载的流程
第7步: dataset/...             ← 需要自定义数据集时再来
```

---

*创建于: 2026-07-09*
*配套 OKR 任务: D3 — ms-swift 框架入门*
