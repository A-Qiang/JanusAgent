# 数据集

## 数据结构

```
data/
├── train.jsonl          # 训练集（ms-swift JSONL 格式）
├── val.jsonl            # 验证集
├── test.jsonl           # 测试集
├── images/              # 图像文件（可选）
└── data_report.md       # 数据预览报告
```

## JSONL 格式（ms-swift OCR template）

```json
{
  "messages": [
    {"role": "user", "content": "<image>\n请识别图片中的内容"},
    {"role": "assistant", "content": "识别的文本..."}
  ],
  "images": ["path/to/image.png"]
}
```

## 数据来源

推荐初始数据集：
- [LaTeX_OCR](https://huggingface.co/datasets/lmms-lab/LaTeX_OCR) — 公式识别
- 自定义文档扫描件 + OCR 标注

准备命令：

```bash
python scripts/prepare_data.py --source hf://lmms-lab/LaTeX_OCR --output-dir data --report
```
