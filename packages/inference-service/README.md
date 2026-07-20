# inference-service

**JanusAgent** 的统一模型推理服务 —— 在 **SGLang**、**vLLM** 和 **Transformers** 之上提供一致的模型服务层，依赖极少。

## 架构

```
┌─────────────────────────────────────────────────┐
│                 inference-service                │
│                                                   │
│  ┌──────────┐   ┌────────────────────────────┐   │
│  │  Client  │──▶│     FastAPI Server (:31001) │   │
│  │  SDK     │   │  ┌──────────┐ ┌──────────┐ │   │
│  └──────────┘   │  │ /health  │ │ /v1/*    │ │   │
│                  │  └──────────┘ └──────────┘ │   │
│                  └────────┬───────────────────┘   │
│                           │                       │
│                  ┌────────▼───────────────────┐   │
│                  │     ServiceEngine (ABC)     │   │
│                  │  ┌──────────┐ ┌──────────┐ ┌────────────────┐ │   │
│                  │  │  SGLang  │ │   vLLM   │ │  Transformers  │ │   │
│                  │  │  Engine  │ │  (代理)  │ │     Engine     │ │   │
│                  │  └──────────┘ └──────────┘ └────────────────┘ │   │
│                  └────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**核心设计思路**：

- **管理面**（31001 端口）与 **数据面**（30001 端口）分离，运维人员可访问管理 API 而无需暴露模型端点。
- **引擎抽象层**（`ServiceEngine` 抽象基类、`EngineConfig`、`EngineState`）让应用切换后端时无需改动服务代码。
- **SGLang 后端**：启动并管理嵌入式 `sglang.Runtime` 子进程。
- **vLLM 后端**：采用**代理模式**，假定已有运行中的 vLLM 服务器，通过 HTTP 与之通信。
- **Transformers 后端**：原生加载 HuggingFace `AutoModelForCausalLM`，支持自定义架构（`trust_remote_code=True`），适用于 SGLang/vLLM 不支持的模型。

## 目录结构

```
src/inference_service/
├── __init__.py          # 包元信息、版本号
├── __main__.py          # CLI 入口（uvicorn 启动器）
├── client/
│   ├── __init__.py
│   └── client.py        # 异步 HTTP 客户端 SDK（chat / complete / health）
├── engine/
│   ├── __init__.py      # 公开导出：create_engine, EngineConfig 等
│   ├── base.py          # ServiceEngine 抽象基类, EngineConfig, EngineState
│   ├── sglang_engine.py     # SGLang Runtime 子进程管理器
│   ├── sglang_router.py     # 引擎工厂方法（后端选择）
│   ├── transformers_engine.py  # Transformers 原生推理引擎
│   └── vllm_engine.py     # vLLM 代理（远端 HTTP 客户端）
└── server/
    ├── __init__.py      # 公开导出：ServiceConfig, create_app
    ├── app.py           # FastAPI 应用工厂
    ├── config.py        # ServiceConfig（CLI / 环境变量 / 文件，基于 Pydantic-Settings）
    ├── middleware.py    # 请求延迟日志中间件
    └── routes.py        # 管理 API 路由
```

## 快速开始

### 前置条件

- Python ≥ 3.12
- CUDA 12.4+ 环境（用于 GPU 推理）
- `accelerate`（Transformers 后端需要：`uv pip install accelerate`）

### 安装

```bash
# 确保已安装 uv：curl -LsSf https://astral.sh/uv/install.sh | sh

# 基础安装（不含 SGLang/vLLM 可选依赖）
uv sync

# 如需 SGLang 支持
uv sync --extra sglang

# 如需 vLLM 支持
uv sync --extra vllm

# 如需完整开发环境
uv sync --group dev
```

### 启动服务

```bash
# --- Transformers 后端（推荐用于自定义架构或小模型）---
inference-service --backend transformers --model_path /data/models/MiniMind-3/

# --- SGLang 后端（高性能推理）---
inference-service --backend sglang --model_path /data/models/MiniMind-3/

# --- vLLM 代理模式（连接远端 vLLM 服务器）---
inference-service --backend vllm --vllm_base_url http://127.0.0.1:8000 --vllm_api_key xxx
```

### Docker Compose 运行

```bash
MODEL_PATH=/data/models/MiMo-V2.5/ docker compose up -d
```

详见 [`docker-compose.yml`](./docker-compose.yml)。

### CLI / 环境变量配置

所有设置项均支持 CLI 参数或以 `INFERENCE_` 为前缀的环境变量。

| 参数 | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `--backend` | `INFERENCE_BACKEND` | `sglang` | 推理引擎后端（`sglang` \| `vllm` \| `transformers`） |
| `--model_path` | `INFERENCE_MODEL_PATH` | （必填） | HuggingFace 模型 ID 或本地路径 |
| `--host` | `INFERENCE_HOST` | `0.0.0.0` | 绑定地址 |
| `--port` | `INFERENCE_PORT` | `30001` | 引擎数据面端口 |
| `--management_port` | `INFERENCE_MANAGEMENT_PORT` | `31001` | 管理 API 端口 |
| `--dtype` | `INFERENCE_DTYPE` | `auto` | 权重数据类型 |
| `--max_model_len` | `INFERENCE_MAX_MODEL_LEN` | （后端默认） | 最大序列长度 |
| `--gpu_memory_utilization` | `INFERENCE_GPU_MEMORY_UTILIZATION` | `0.90` | GPU 内存占比 |
| `--vllm_base_url` | `INFERENCE_VLLM_BASE_URL` | — | 远程 vLLM 地址（vLLM 代理模式） |
| `--vllm_api_key` | `INFERENCE_VLLM_API_KEY` | — | vLLM 认证令牌 |

## API

所有管理端点在 **31001 端口**提供服务。

### `GET /health`

引擎健康状态与生命周期状态。

```json
{
  "status": "healthy",
  "engine_state": "ready",
  "model": "/data/models/MiMo-V2.5/",
  "endpoint": "http://127.0.0.1:30001"
}
```

### `GET /v1/models`

已注册模型的元信息。

```json
{
  "object": "list",
  "data": [
    { "id": "/data/models/MiMo-V2.5/", "object": "model", "backend": "sglang" }
  ]
}
```

## 客户端 SDK

JanusAgent 的其他包可导入 `InferenceClient` 进行服务间通信：

```python
from inference_service.client import InferenceClient

async with InferenceClient("http://inference-service:31001") as client:
    health = await client.health()
    reply = await client.chat([
        {"role": "user", "content": "你好！"},
    ])
    completion = await client.complete("从前有座山")
```

## 部署指南

### MiniMind-3（标准 Qwen3 架构，~122MB）

```bash
CUDA_VISIBLE_DEVICES=1 .venv/bin/python -m inference_service \
  --backend transformers \
  --model_path /data/models/minimind-3/ \
  --host 127.0.0.1 \
  --management_port 31001 \
  --dtype float16 \
  --gpu_memory_utilization 0.6
```

- 架构：`Qwen3ForCausalLM`（标准 HF，无需 `trust_remote_code`）
- VRAM：~0.16 GB（单 GPU 即可）
- 管理 API：`http://127.0.0.1:31001`
- 注意事项：SGLang 后端因 `sgl_kernel` 与 torch 2.11 的 ABI 不兼容而暂时不可用，请使用 transformers 后端。

### MiMo-V2.5（自定义架构，~290GB）

```bash
CUDA_VISIBLE_DEVICES=1,2,3 .venv/bin/python -m inference_service \
  --backend transformers \
  --model_path /data/models/MiMo-V2.5/ \
  --host 127.0.0.1 \
  --management_port 31002 \
  --dtype float16 \
  --gpu_memory_utilization 0.95
```

- 架构：`MiMoV2ForCausalLM`（自定义 MoE 架构，需 `trust_remote_code=True`，由 engines backend 自动处理）
- 权重：16 个 safetensors 分片（PP+EP），总计约 290GB
- GPU：建议 3× H20（各 ~97GB），`device_map="auto"` 配合 accelerate 自动分配
- ⚠️ SGLang/vLLM 均不支持该自定义架构——必须使用 `transformers` 后端

### 验证部署

```bash
# 健康检查
curl -s http://127.0.0.1:31001/health | jq .

# 模型列表
curl -s http://127.0.0.1:31001/v1/models | jq .

# 对话补全
curl -s http://127.0.0.1:31001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "minimind-3",
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 128
  }' | jq .
```

## 已知兼容性问题

| 问题 | 表现 | 解决 |
|------|------|------|
| `vllm==0.25.1` 导入错误 | `ImportError: cannot import name 'NamespaceTool' from 'openai.types.responses'` | 降级 vLLM 到 `0.24.0` |
| `sgl_kernel` ABI 不匹配 | `undefined symbol: c10_cuda_check_implementation`（需要 torch 版本与 sgl_kernel 编译版本一致） | 等待 sgl_kernel 发布兼容 torch 2.11 的版本；临时使用 transformers 后端 |
| `accelerate` 未安装 | `Using a device_map requires accelerate` | `uv pip install accelerate` |

## 开发

```bash
# 安装包含开发依赖
uv sync --group dev

# 本地运行
uv run inference-service --model_path /data/models/MiMo-V2.5/
```
