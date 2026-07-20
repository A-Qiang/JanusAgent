# 实验目录

每次实验在 `experiments/` 下新建一个子目录：

```
experiments/
├── exp-001/               # 第一次 LoRA SFT
│   ├── checkpoint-xxx/    # 模型 checkpoint
│   ├── train.log          # 训练日志
│   ├── loss.csv           # loss 曲线（TensorBoard events 同目录）
│   └── args.json          # 本次实验超参数快照
├── exp-002/               # lr=5e-5 对比实验
└── ...
```

## 命名约定

| 模式 | 含义 |
|------|------|
| `exp-NNN` | 按时间顺序的常规实验 |
| `ablation-lr-5e5` | 特定消融实验 |
| `grpo-run-01` | RLHF / GRPO 实验 |

## 决策记录 (ADR)

每次实验的参数变更应记录在 `experiments/ADRS.md` 中。
