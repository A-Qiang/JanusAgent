#!/usr/bin/env python3
"""
verify_env.py — MinerU2.5 微调环境验证

校验以下组件的版本及可用性：
  - CUDA Toolkit
  - PyTorch
  - Flash Attention
  - ms-swift
  - GPU 可用性 & 显存

用法：
    python scripts/verify_env.py
"""

import importlib.metadata
import platform
import subprocess
import sys
from typing import Any


def fmt_version(pkg: str, version: str | None, ok: bool) -> str:
    icon = "✅" if ok else "❌"
    return f"  {icon} {pkg:24s} {version or 'N/A':20s}"


def check_torch() -> tuple[str | None, bool]:
    try:
        import torch  # noqa: F811
        return torch.__version__, True
    except ImportError:
        return None, False


def check_torch_cuda() -> tuple[bool, int, str | None]:
    try:
        import torch

        available = torch.cuda.is_available()
        if available:
            count = torch.cuda.device_count()
            cap = torch.cuda.get_device_capability()
            gpu_name = torch.cuda.get_device_name(0)
            sm = f"{cap[0]}.{cap[1]}"
            info = f"{gpu_name} × {count} (SM {sm})"
            return True, count, info
        return False, 0, "CUDA not available"
    except Exception as e:
        return False, 0, str(e)


def check_flash_attn() -> tuple[str | None, bool]:
    try:
        import flash_attn  # noqa: F401
        ver = importlib.metadata.version("flash-attn")
        return ver, True
    except ImportError:
        return None, False


def check_ms_swift() -> tuple[str | None, bool]:
    try:
        ver = importlib.metadata.version("ms-swift")
        return ver, True
    except ImportError:
        return None, False


def check_nvcc() -> tuple[str | None, bool]:
    try:
        result = subprocess.run(
            ["nvcc", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            # 提取 "release X.Y" 部分
            for line in result.stdout.splitlines():
                if "release" in line:
                    return line.strip(), True
            return result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ("unknown", True)
        return result.stderr.strip() or "nvcc failed", False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None, False


def check_gpu_memory() -> str | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total,memory.free,memory.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            infos = []
            for i, line in enumerate(result.stdout.strip().splitlines()):
                parts = line.split(", ")
                if len(parts) == 3:
                    total, free_, used = parts
                    infos.append(f"GPU{i}: {used}/{total} MiB used ({free_} MiB free)")
            return ", ".join(infos) if infos else None
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def main():
    print("=" * 60)
    print("  MinerU2.5 微调环境验证")
    print(f"  Python: {platform.python_version()} ({platform.system()} {platform.machine()})")
    print("=" * 60)
    print()

    results: list[dict[str, Any]] = []

    # ---- Python packages ----
    torch_ver, torch_ok = check_torch()
    results.append(("PyTorch", torch_ver, torch_ok))

    flash_ver, flash_ok = check_flash_attn()
    results.append(("Flash Attention", flash_ver, flash_ok))

    swift_ver, swift_ok = check_ms_swift()
    results.append(("ms-swift", swift_ver, swift_ok))

    # 其他关键依赖
    for pkg in ["transformers", "datasets", "accelerate", "sentencepiece", "einops"]:
        try:
            ver = importlib.metadata.version(pkg)
            results.append((pkg, ver, True))
        except ImportError:
            results.append((pkg, None, False))

    print("[Python Packages]")
    for name, ver, ok in results:
        print(fmt_version(name, ver, ok))
    print()

    # ---- CUDA ----
    nvcc_ver, nvcc_ok = check_nvcc()
    print(fmt_version("nvcc (CUDA)", nvcc_ver, nvcc_ok))

    # ---- GPU ----
    cuda_avail, gpu_count, gpu_info = check_torch_cuda()
    print(fmt_version("GPU (torch)", gpu_info, cuda_avail))

    mem_info = check_gpu_memory()
    if mem_info:
        print(f"  ℹ️   Memory:      {mem_info}")
    print()

    # ---- Summary ----
    passed = all(ok for _, _, ok in results[:3]) and cuda_avail
    print("─── Summary ─────────────────────────────────────")
    if passed:
        print("  ✅ 所有核心组件就绪，可以开始微调！")
    else:
        missing = [name for name, _, ok in results[:3] if not ok]
        if not cuda_avail:
            missing.append("CUDA GPU")
        print(f"  ❌ 缺失: {', '.join(missing)}")
        print("     请执行: pip install ms-swift torch flash-attn")
    print()

    if nvcc_ver:
        print("  💡 建议: 若训练中遇到 OOM，可降低 per_device_batch_size")
        print("     或增大 gradient_accumulation_steps")
    print("=" * 60)


if __name__ == "__main__":
    main()
