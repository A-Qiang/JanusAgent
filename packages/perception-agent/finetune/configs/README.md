# 训练配置

| 文件 | 用途 |
|------|------|
| `default.yaml` | LoRA SFT 默认配置（lora_rank=8, lr=1e-4, freeze_vit） |
| `best.yaml` | 最优超参数组合（消融实验后确定） |

使用方式：

```bash
# 使用默认配置
swift sft --config configs/default.yaml

# 命令行覆盖
swift sft --config configs/default.yaml --learning_rate 5e-5
```
