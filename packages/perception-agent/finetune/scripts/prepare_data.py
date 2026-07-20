#!/usr/bin/env python3
"""
prepare_data.py — MinerU2.5 微调数据预处理 Pipeline

功能：
1. 从 HuggingFace / 本地路径读取原始文档数据集
2. 转换为 ms-swift 兼容的 JSONL 格式
3. 按 8:1:1 切分 train / val / test
4. 输出数据预览报告

用法：
    python scripts/prepare_data.py \
        --source hf://lmms-lab/LaTeX_OCR \
        --output-dir ../data \
        --split-ratio 0.8 0.1 0.1 \
        --report

JSONL 格式要求（ms-swift OCR template）：
    {"messages": [
        {"role": "user", "content": "<image>\n请识别图片中的内容"},
        {"role": "assistant", "content": "识别的文字内容..."}
    ], "images": ["path/to/image.png"]}
"""

import argparse
import json
import logging
import os
from collections import Counter
from pathlib import Path

import jsonlines
from PIL import Image
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "<image>\n请仔细识别图片中的所有文字和版面信息，输出结构化的排版结果。"


def parse_args():
    parser = argparse.ArgumentParser(description="MinerU2.5 微调数据预处理")
    parser.add_argument("--source", type=str, required=True,
                        help="数据源路径，支持 hf://<dataset> 或本地目录")
    parser.add_argument("--output-dir", type=str, default="../data",
                        help="输出目录")
    parser.add_argument("--split-ratio", type=float, nargs=3, default=[0.8, 0.1, 0.1],
                        help="train / val / test 比例")
    parser.add_argument("--report", action="store_true",
                        help="生成数据预览报告")
    parser.add_argument("--sample-limit", type=int, default=None,
                        help="限制处理的样本数（调试用）")
    return parser.parse_args()


def convert_to_ms_swift_format(image_path: str, ground_truth: str) -> dict:
    """将原始数据条目转为 ms-swift OCR template 格式。"""
    return {
        "messages": [
            {"role": "user", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": ground_truth},
        ],
        "images": [image_path],
    }


def load_from_hf(source: str, sample_limit: int | None = None):
    """从 HuggingFace Datasets 加载数据集。"""
    import datasets

    dataset_name = source.replace("hf://", "")
    logger.info("Loading dataset: %s", dataset_name)
    ds = datasets.load_dataset(dataset_name, split="train", trust_remote_code=True)
    if sample_limit:
        ds = ds.select(range(min(sample_limit, len(ds))))
    logger.info("Loaded %d samples from %s", len(ds), dataset_name)
    return ds


def load_from_local(source: str, sample_limit: int | None = None):
    """从本地目录加载数据集（假设每张图片对应同名的 .txt/.md 标注文件）。"""
    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")

    records = []
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

    for img_file in sorted(source_path.iterdir()):
        if img_file.suffix.lower() not in image_extensions:
            continue

        # 寻找同名标注文件
        label_file = img_file.with_suffix(".txt")
        if not label_file.exists():
            label_file = img_file.with_suffix(".md")
        if not label_file.exists():
            logger.warning("No label file found for %s, skipping", img_file.name)
            continue

        with open(label_file, "r", encoding="utf-8") as f:
            gt_text = f.read().strip()

        records.append({
            "image_path": str(img_file.resolve()),
            "ground_truth": gt_text,
        })

        if sample_limit and len(records) >= sample_limit:
            break

    logger.info("Loaded %d samples from local path: %s", len(records), source)
    return records


def write_jsonl(records: list, output_path: Path):
    """将记录写入 JSONL 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonlines.open(str(output_path), mode="w") as writer:
        for rec in records:
            writer.write(rec)
    logger.info("Written %d entries to %s", len(records), output_path)


def generate_report(train: list, val: list, test: list, output_dir: Path):
    """生成数据预览报告。"""
    report_lines = []
    report_lines.append("# 数据预览报告\n")
    report_lines.append(f"| 子集 | 样本数 | 占比 |")
    report_lines.append(f"|------|--------|------|")
    report_lines.append(f"| Train | {len(train)} | {len(train)/(len(train)+len(val)+len(test)):.1%} |")
    report_lines.append(f"| Val   | {len(val)} | {len(val)/(len(train)+len(val)+len(test)):.1%} |")
    report_lines.append(f"| Test  | {len(test)} | {len(test)/(len(train)+len(val)+len(test)):.1%} |")
    report_lines.append(f"| Total | {len(train)+len(val)+len(test)} | 100% |")

    # 统计图像分辨率
    resolutions = []
    for split_data, split_name in [(train, "train"), (val, "val"), (test, "test")]:
        for rec in tqdm(split_data, desc=f"Analyzing {split_name}"):
            img_path = rec.get("images", [None])[0] if isinstance(rec.get("images"), list) else rec.get("images")
            if img_path and os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    resolutions.append((img.width, img.height))
                except Exception:
                    pass

    if resolutions:
        widths = [w for w, _ in resolutions]
        heights = [h for _, h in resolutions]
        report_lines.append("\n## 图像分辨率分布\n")
        report_lines.append(f"- 样本数: {len(resolutions)}")
        report_lines.append(f"- 宽度范围: {min(widths)}–{max(widths)}")
        report_lines.append(f"- 高度范围: {min(heights)}–{max(heights)}")
        report_lines.append(f"- 平均分辨率: {sum(widths)//len(widths)}×{sum(heights)//len(heights)}")

    report_path = output_dir / "data_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    logger.info("Report saved to %s", report_path)


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 加载 ----------
    if args.source.startswith("hf://"):
        raw_records = load_from_hf(args.source, args.sample_limit)
    else:
        raw_records = load_from_local(args.source, args.sample_limit)

    # ---------- 转换 ----------
    converted = []
    for rec in raw_records:
        if isinstance(rec, dict) and "image_path" in rec:
            record = convert_to_ms_swift_format(rec["image_path"], rec["ground_truth"])
        elif isinstance(rec, dict) and "images" in rec:
            # 已经是 ms-swift 格式
            record = rec
        else:
            logger.debug("Skipping unrecognized record format: %s", type(rec))
            continue
        converted.append(record)

    logger.info("Converted %d records to ms-swift format", len(converted))

    if not converted:
        logger.error("No valid records after conversion. Aborting.")
        return

    # ---------- 切分 ----------
    train_ratio, val_ratio, test_ratio = args.split_ratio
    n = len(converted)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    n_test = n - n_train - n_val

    train_data = converted[:n_train]
    val_data = converted[n_train:n_train + n_val]
    test_data = converted[n_train + n_val:]

    # ---------- 写出 ----------
    write_jsonl(train_data, output_dir / "train.jsonl")
    write_jsonl(val_data, output_dir / "val.jsonl")
    write_jsonl(test_data, output_dir / "test.jsonl")

    # ---------- 报告 ----------
    if args.report:
        generate_report(train_data, val_data, test_data, output_dir)

    logger.info("Done! Data ready at %s", output_dir.absolute())
    logger.info("Tip: use `swift sft --dataset %s/train.jsonl` to start training",
                output_dir.absolute())


if __name__ == "__main__":
    main()
