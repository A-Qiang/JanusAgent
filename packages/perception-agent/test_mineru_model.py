#!/usr/bin/env python3
"""
MinerU2.5-Pro-2605-1.2B 模型测试脚本
=======================================
用法:
    # 默认模式（自动选择后端）
    python test_mineru_model.py /path/to/document.png

    # 指定后端
    python test_mineru_model.py /path/to/document.png --backend transformers
    python test_mineru_model.py /path/to/document.png --backend raw

    # 查看设备信息
    python test_mineru_model.py --info

    # 仅测试模型加载
    python test_mineru_model.py --dry-run
"""

import argparse
import os
import sys
import time

MODEL_PATH = "/home/zengqiang/models/MinerU2.5-Pro-2605-1.2B"


def print_sep(title=""):
    width = 70
    print()
    if title:
        left = (width - len(title) - 2) // 2
        right = width - len(title) - 2 - left
        print("=" * left, title, "=" * right)
    else:
        print("=" * width)


def check_device():
    """检测可用设备"""
    try:
        import torch
        if torch.cuda.is_available():
            device = f"cuda:{torch.cuda.current_device()} ({torch.cuda.get_device_name()})"
            mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            return device, f"{mem:.1f} GB"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps", "MPS (Apple Silicon)"
        else:
            return "cpu", "CPU"
    except ImportError:
        return "unknown", "torch not installed"


def check_deps():
    """检查依赖安装情况"""
    deps = {}
    for mod_name, pip_name in [
        ("torch", "torch"),
        ("transformers", "transformers"),
        ("accelerate", "accelerate"),
        ("mineru_vl_utils", "mineru-vl-utils"),
        ("vllm", "vllm"),
        ("PIL", "pillow"),
    ]:
        try:
            mod = __import__(mod_name.replace("_", "."))
            ver = getattr(mod, "__version__", "installed")
            deps[pip_name] = ver
        except ImportError:
            deps[pip_name] = None
    return deps


def show_info():
    """显示系统和模型信息"""
    print_sep("System Info")
    device, mem = check_device()
    print(f"  Device:        {device}")
    print(f"  Memory:        {mem}")

    print_sep("Dependencies")
    deps = check_deps()
    for name, ver in deps.items():
        status = f"\033[32m{ver}\033[0m" if ver else "\033[31mNOT INSTALLED\033[0m"
        print(f"  {name:<24} {status}")

    print_sep("Model Info")
    if os.path.exists(MODEL_PATH):
        files = os.listdir(MODEL_PATH)
        safetensors = [f for f in files if f.endswith(".safetensors")]
        total_size = sum(
            os.path.getsize(os.path.join(MODEL_PATH, f))
            for f in safetensors if os.path.isfile(os.path.join(MODEL_PATH, f))
        ) / (1024**3)
        print(f"  Path:          {MODEL_PATH}")
        print(f"  Weight Files:  {len(safetensors)} ({total_size:.1f} GB)")
        print(f"  Config:        {'config.json' in files}")
        print(f"  Tokenizer:     {'tokenizer.json' in files}")
    else:
        print(f"  \033[31mERROR: Model path not found: {MODEL_PATH}\033[0m")

    print()


def verify_image(path):
    """验证图片文件"""
    if not os.path.exists(path):
        print(f"\033[31mError: File not found: {path}\033[0m")
        sys.exit(1)

    from PIL import Image
    try:
        img = Image.open(path)
        img.verify()
        img = Image.open(path)
        print(f"  Image:         {path}")
        print(f"  Size:          {img.size[0]}x{img.size[1]}")
        print(f"  Mode:          {img.mode}")
        return img
    except Exception as e:
        print(f"\033[31mError: Invalid image file: {e}\033[0m")
        sys.exit(1)


def create_test_image(width=800, height=500):
    """创建一张简单的测试图片（白底黑字）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("\033[31mPillow required: pip install pillow\033[0m")
        sys.exit(1)

    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "MinerU2.5-Pro Model Test", fill=(0, 0, 0))
    draw.text((50, 100), "==========================", fill=(0, 0, 0))
    draw.text((50, 130), "This is a test document page.", fill=(0, 0, 0))
    draw.text((50, 170), "Section 1: Introduction", fill=(0, 0, 0))
    draw.text((50, 200), "  MinerU2.5-Pro is a document parsing model.", fill=(0, 0, 0))
    draw.text((50, 230), "  It converts PDF/images to Markdown format.", fill=(0, 0, 0))
    draw.text((50, 270), "Section 2: Features", fill=(0, 0, 0))
    draw.text((50, 300), "  - Text Recognition", fill=(0, 0, 200))
    draw.text((50, 330), "  - Table Parsing (TEDS 93.62)", fill=(0, 100, 0))
    draw.text((50, 360), "  - Formula Recognition (CDM 97.15)", fill=(100, 0, 0))
    draw.text((50, 390), "  Performance Test: Hello World 42", fill=(0, 0, 0))

    temp_path = "/tmp/mineru_test_input.png"
    img.save(temp_path)
    print(f"  Generated test image: {temp_path}")
    return temp_path


def test_raw_transformers(image_path, args):
    """
    使用原生 transformers（不依赖 mineru-vl-utils）。
    直接用 Qwen2VL 的 chat template 进行对话式推理。
    """
    import torch
    from transformers import (
        AutoProcessor,
        Qwen2VLForConditionalGeneration,
    )

    print_sep("Loading Model (raw transformers)")
    t0 = time.time()

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="flash_attention_2",
    )
    processor = AutoProcessor.from_pretrained(MODEL_PATH, use_fast=True)

    print(f"  Load time:     {time.time() - t0:.1f}s")
    print(f"  Params:        {model.num_parameters() / 1e9:.2f}B")

    img = Image.open(image_path)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": img},
                {"type": "text", "text": args.prompt or "Please parse this document page into Markdown format."},
            ],
        }
    ]

    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[prompt], images=[img], padding=True, return_tensors="pt")
    inputs = {k: v.to(model.device) if hasattr(v, "to") else v for k, v in inputs.items()}

    print_sep("Inference")
    t0 = time.time()
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
        )
    elapsed = time.time() - t0

    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    tokens_generated = generated_ids_trimmed[0].shape[0]
    print(f"  Time:          {elapsed:.1f}s")
    print(f"  Tokens:        {tokens_generated} ({tokens_generated / elapsed:.1f} tok/s)")
    print()
    print("=" * 70)
    print("OUTPUT:")
    print("=" * 70)
    print(output_text)
    print("=" * 70)

    return output_text


def test_mineru_client(image_path, args):
    """
    使用 mineru-vl-utils 提供的 MinerUClient（推荐方式）。
    支持 two_step_extract 和 json2md 转换。
    """
    from PIL import Image
    from mineru_vl_utils import MinerUClient

    print_sep("Loading Model (mineru-vl-utils)")
    t0 = time.time()

    client = MinerUClient(
        backend="transformers",
        model_name_or_path=MODEL_PATH,
        image_analysis=args.image_analysis,
    )

    print(f"  Load time:     {time.time() - t0:.1f}s")

    img = Image.open(image_path)

    print_sep("Inference (two_step_extract)")
    t0 = time.time()
    result = client.two_step_extract(img)
    elapsed = time.time() - t0

    print(f"  Time:          {elapsed:.1f}s")
    print()
    print("=" * 70)
    print("RAW OUTPUT (content_list):")
    print("=" * 70)
    print(result)
    print("=" * 70)

    # Convert to Markdown if available
    try:
        from mineru_vl_utils.post_process import json2md
        md = json2md(result)
        print_sep("Markdown Output")
        print(md)
        print("=" * 70)
    except ImportError:
        print("\n(Install mineru-vl-utils with post_process for markdown conversion)")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="MinerU2.5-Pro-2605-1.2B Model Test Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/page.png
  %(prog)s /path/to/page.png --backend raw
  %(prog)s /path/to/page.png --prompt "Extract all tables"
  %(prog)s --dry-run              # 只加载模型，不推理
  %(prog)s --info                  # 显示环境信息
  %(prog)s                         # 用生成的测试图按优先级尝试后端
""",
    )
    parser.add_argument("image", nargs="?", default=None, help="Input document image path")
    parser.add_argument("--backend", choices=["auto", "mineru", "raw", "transformers"],
                        default="auto", help="Backend to use (default: auto)")
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt for the model (default: parse to markdown)")
    parser.add_argument("--max-tokens", type=int, default=1024,
                        help="Max new tokens to generate (default: 1024)")
    parser.add_argument("--image-analysis", action="store_true",
                        help="Enable image/chart analysis mode (mineru client only)")
    parser.add_argument("--info", action="store_true",
                        help="Show system info and exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only load model, skip inference")
    parser.add_argument("--tiny", action="store_true",
                        help="Generate a tiny test image instead of requiring one")

    args = parser.parse_args()

    # --info 仅展示信息
    if args.info:
        show_info()
        return

    # --dry-run 仅加载模型
    if args.dry_run:
        if not os.path.exists(MODEL_PATH):
            print(f"\033[31mError: Model path not found: {MODEL_PATH}\033[0m")
            sys.exit(1)
        show_info()
        print_sep("Dry Run - Loading Model")
        from transformers import AutoConfig
        cfg = AutoConfig.from_pretrained(MODEL_PATH)
        print(f"  Architecture:  {cfg.architectures}")
        print(f"  Model Type:    {cfg.model_type}")
        print(f"  Hidden Size:   {cfg.hidden_size}")
        print(f"  Layers:        {cfg.num_hidden_layers}")
        print(f"  Heads:         {cfg.num_attention_heads}")
        print(f"  Vocab Size:    {cfg.vocab_size}")
        print(f"  Max Position:  {cfg.max_position_embeddings}")
        print(f"\n  \033[32m✓ Model config loaded successfully.\033[0m")
        return

    # 准备输入图片
    if args.image:
        image_path = args.image
        verify_image(image_path)
    elif args.tiny:
        image_path = create_test_image()
        print(f"  \033[33mUsing generated test image.\033[0m")
    else:
        print("\033[33mNo image provided. Generating a test image...\033[0m")
        image_path = create_test_image()

    from PIL import Image

    # 决定后端
    deps = check_deps()
    backend = args.backend

    if backend == "auto":
        if deps.get("mineru-vl-utils"):
            backend = "mineru"
            print("  \033[32mAuto-select: mineru-vl-utils (MinerUClient)\033[0m")
        else:
            backend = "raw"
            print("  \033[33mAuto-select: raw transformers (mineru-vl-utils not installed)\033[0m")
            print("  \033[33m  Install: pip install 'mineru-vl-utils[transformers]'\033[0m")
    elif backend == "transformers":
        backend = "raw"

    if backend == "mineru":
        if not deps.get("mineru-vl-utils"):
            print("\033[31mError: mineru-vl-utils not installed.\033[0m")
            print("  pip install 'mineru-vl-utils[transformers]'")
            sys.exit(1)
        if not deps.get("transformers"):
            print("\033[31mError: transformers not installed.\033[0m")
            sys.exit(1)
        test_mineru_client(image_path, args)
    else:
        if not deps.get("transformers"):
            print("\033[31mError: transformers not installed.\033[0m")
            print("  pip install 'transformers>=4.56.0'")
            sys.exit(1)
        test_raw_transformers(image_path, args)

    print_sep("Done")


if __name__ == "__main__":
    main()
