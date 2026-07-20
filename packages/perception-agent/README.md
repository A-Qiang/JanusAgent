# perception-agent

**JanusAgent 多模感知层** — 解决大模型的知识摄入（Knowledge Ingestion）问题。

提供统一的感知抽象层，将多模态输入（文档、图片、音频、视频）转化为结构化知识，供 JanusAgent 内核消费。

## 设计

```
Core 抽象层  →  Ingestion Providers  →  Chunking  →  Embedding  →  Store
(BasePerceptor)  (文档/图像/音频/视频)    (分块策略)    (嵌入适配)    (结构化存储)
```

遵循 Provider 模式 — Core 定义感知契约，各 Provider 独立实现，可插拔替换。

## 开发

```bash
# 安装依赖
uv sync

# 运行
uv run perception-agent
```

## 模型测试

项目附带了一个 MinerU2.5-Pro-2605-1.2B 文档解析模型的测试脚本。

> **注意**：由于环境下 `cpython-3.13.14` 的 gzip 缓存损坏，`uv run` 需强制指定 Python 3.12。

### 环境检查

```bash
# 方式一：激活 venv 后直接运行
source /home/zengqiang/projects/JanusAgent/.venv/bin/activate
python test_mineru_model.py --info

# 方式二：使用 uv run（必须加 --python 3.12）
uv run --python 3.12 python test_mineru_model.py --info
```

### 快速测试（生成测试图片）

```bash
# 使用原生 transformers 后端（推荐）
python test_mineru_model.py --tiny --backend raw

# 输出保存到文件
python test_mineru_model.py --tiny --backend raw -o result.md
```

### 使用自己的图片
| "/home/zengqiang/data/SAC1200E3/Sany-photo-SAC1200E3.jpg"

```bash
python test_mineru_model.py /path/to/your/image.png --backend raw
python test_mineru_model.py /path/to/your/image.png --backend raw -o result.md
```

### 可选参数

| 参数 | 说明 |
|------|------|
| `--backend raw` | 原生 transformers 后端（稳定） |
| `--backend mineru` | mineru-vl-utils 后端 |
| `--backend auto` | 自动选择（默认） |
| `--prompt TEXT` | 自定义提示词 |
| `--max-tokens N` | 最大生成 token 数（默认 1024） |
| `-o, --output FILE` | 输出保存到文件 |
| `--dry-run` | 仅加载模型配置，不推理 |
| `--info` | 查看系统和依赖信息 |
| `--tiny` | 生成测试图片代替手动传入 |

## Docker 部署

MinerU API 服务支持通过 Docker Compose 一键部署管理，配置文件见 [docker-compose.yml](./docker-compose.yml)。

### 前置条件

```bash
# 1. 构建 MinerU 镜像（首次或 Dockerfile 变更时执行）
docker build -t mineru:latest -f MinerU/docker/china/Dockerfile .

# 2. 确认空闲 GPU 编号
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader
```

### 启动 / 重启 / 停止

```bash
# 启动（后台运行）
docker compose up -d

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 停止并删除容器（数据卷保留）
docker compose down

# 修改代码后重新构建并启动
docker compose up -d --build
```

### 可配置项

通过环境变量或 `.env` 文件覆盖默认配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `GPU_DEVICE_ID` | `1` | 钉定的物理 GPU 编号（**不可用 all**，vLLM 默认占 cuda:0） |
| `MINERU_MAX_CONCURRENT` | `8` | 并发解析任务上限（MinerU 默认仅 3） |
| `MINERU_PORT_API` | `8001` | 宿主机 API 访问端口（容器内固定 8000） |
| `MINERU_PORT_VLM` | `30000` | vLLM OpenAI 兼容服务端口 |
| `MINERU_PORT_GRADIO` | `7860` | Gradio UI 端口 |
| `MINERU_PORT_EXTRA` | `8002` | 备用端口 |
| `MINERU_WORKSPACE` | `/data/zengqiang/mineru-workspace` | 解析结果输出目录 |

```bash
# 示例：换用 GPU 2 + 并发提到 16
GPU_DEVICE_ID=2 MINERU_MAX_CONCURRENT=16 docker compose up -d
```

### 验证

```bash
# 健康检查
curl -s http://localhost:8001/health
# 期望: {"status":"ok", "max_concurrent_requests": 8}

# API 文档
# 浏览器打开 http://localhost:8001/docs
```

> 详细 API 接口说明见 [MinerU API 使用说明](./docs/guide/mineru使用说明.md)。
