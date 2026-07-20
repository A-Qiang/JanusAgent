# MinerU2.5 微调管线

> 基于 ms-swift 对 MinerU2.5 进行 LoRA SFT 微调。

## 目录结构

```
finetune/
├── configs/          # 训练配置 YAML
│   ├── default.yaml  # 默认 LoRA SFT 配置
│   └── best.yaml     # （待定）最佳超参组合
├── data/             # 数据集（JSONL + images）
│   ├── train.jsonl
│   ├── val.jsonl
│   └── test.jsonl
├── scripts/          # 工具脚本
│   ├── prepare_data.py   # 数据预处理
│   └── verify_env.py     # 环境验证
├── experiments/      # 实验产物（checkpoints、logs）
└── pyproject.toml    # 依赖管理
```

## 快速开始

```bash
# 1. 安装依赖
cd finetune/
pip install -e .

# 2. 验证环境
python scripts/verify_env.py

# 3. 准备数据
python scripts/prepare_data.py \
    --source hf://lmms-lab/LaTeX_OCR \
    --output-dir data \
    --report

# 4. 开始训练
swift sft --config configs/default.yaml
```

## Acceptance Criteria

- [ ] `cd finetune/ && pip install -e .` 无报错
- [ ] `python scripts/prepare_data.py` 产出一条格式正确的 JSONL
- [ ] `swift sft --dataset` 能识别生成的 JSONL
