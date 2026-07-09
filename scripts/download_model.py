#!/usr/bin/env python3
"""
模型下载脚本 —— 从 ModelScope 下载指定模型到本地目录。

用法:
    python scripts/download_model.py                          # 下载默认模型
    python scripts/download_model.py --model <model_id>       # 下载指定模型
    python scripts/download_model.py --local-dir <路径>       # 指定保存目录
    python scripts/download_model.py --help                   # 查看帮助
"""

import argparse
import os
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="从 ModelScope 下载模型到本地目录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                                      # 下载 MinerU2.5-Pro-2605-1.2B
  %(prog)s --model Qwen/Qwen2.5-7B-Instruct                    # 下载其他模型
  %(prog)s --local-dir /data/models/qwen                       # 指定保存路径
  %(prog)s --revision v1.0                                      # 指定版本
        """,
    )
    parser.add_argument(
        "--model",
        type=str,
        default="OpenDataLab/MinerU2.5-Pro-2605-1.2B",
        help="ModelScope 模型 ID（默认：OpenDataLab/MinerU2.5-Pro-2605-1.2B）",
    )
    parser.add_argument(
        "--local-dir",
        type=str,
        default="/home/zengqiang/models/MinerU2.5-Pro-2605-1.2B",
        help="模型下载保存路径（默认：/home/zengqiang/models/MinerU2.5-Pro-2605-1.2B）",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="模型版本号/分支名（可选，默认为 master）",
    )
    parser.add_argument(
        "--ignore-patterns",
        type=str,
        nargs="*",
        default=None,
        help="忽略的文件模式列表，例如 --ignore-patterns '*.safetensors' '*.bin'",
    )
    parser.add_argument(
        "--allow-patterns",
        type=str,
        nargs="*",
        default=None,
        help="仅下载匹配这些模式的文件，例如 --allow-patterns '*.json' 'tokenizer*'",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="ModelScope 访问令牌（私有模型需要，从 https://modelscope.cn/my/myaccesstoken 获取）",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="静默模式，不输出进度信息",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.model:
        print("❌ 错误：--model 不能为空")
        sys.exit(1)

    # 创建目标目录
    os.makedirs(args.local_dir, exist_ok=True)

    # 导入 modelscope 库
    try:
        from modelscope.hub.snapshot_download import snapshot_download
    except ImportError:
        print("❌ 缺少依赖：modelscope，正在安装...")
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "modelscope", "--quiet"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"❌ 安装失败：{result.stderr}")
            sys.exit(1)
        from modelscope.hub.snapshot_download import snapshot_download

    print(f"📦 开始下载模型：{args.model}")
    print(f"📂 保存路径：{args.local_dir}")
    if args.revision:
        print(f"🏷️  版本：{args.revision}")
    print()

    kwargs = {
        "model_id": args.model,
        "local_dir": args.local_dir,
        "local_files_only": False,
    }

    if args.revision:
        kwargs["revision"] = args.revision
    if args.ignore_patterns:
        kwargs["ignore_patterns"] = args.ignore_patterns
    if args.allow_patterns:
        kwargs["allow_patterns"] = args.allow_patterns
    if args.token:
        kwargs["token"] = args.token

    try:
        result_path = snapshot_download(**kwargs)
        print()
        print(f"✅ 下载完成！模型保存在：{result_path}")
    except Exception as e:
        print(f"\n❌ 下载失败：{e}")
        print("\n可能的原因：")
        print("  - 网络不通或无法访问 modelscope.cn")
        print("  - 模型 ID 不存在")
        print("  - 指定了错误的版本号")
        print("  - 私有模型但未提供有效的 --token")
        sys.exit(1)


if __name__ == "__main__":
    main()
