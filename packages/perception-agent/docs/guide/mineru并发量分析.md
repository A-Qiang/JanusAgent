# MinerU 容器并发量分析

> 分析对象：`mineru:latest` 容器（MinerU v3.4.4）  
> 分析方法：源码静态分析 + 运行时 `/health`、`docker inspect`、容器内进程与 vLLM 启动日志实证  
> 配套文档：[mineru使用说明.md](./mineru使用说明.md)

---

## 0. 一句话结论

**当前容器启动后的最大并发量 = 3 个并发解析任务。**

这不是硬件瓶颈，而是 MinerU 软件层的默认配置值。服务器硬件（H20×8、1TB 内存、192 核 CPU）远未跑满。

---

## 1. 服务器硬件清单

| 资源 | 配置 | 备注 |
|------|------|------|
| GPU | 8 × NVIDIA H20（每张 97GB VRAM） | 见下表实际占用 |
| CPU | 192 核 Intel Xeon Platinum 8469C | 不构成限制 |
| 内存 | 1TB | 不构成限制 |
| 共享内存 | 容器 `--shm-size 32g` | 不构成限制 |

### 1.1 GPU 实际占用（分析时刻）

| GPU | 显存占用 | 进程 | 归属 |
|------|---------|------|------|
| 0 | 83.5GB | `sglang::scheduler` | 非 MinerU，其他业务 |
| **1** | **49.9GB** | **`VLLM::EngineCore`** | **MinerU 容器（本分析对象）** |
| 2–7 | 0GB | — | **6 张卡完全空闲** |

> ⚠️ `mineru使用说明.md` 中的启动命令写的是 `--gpus all`，但**实际运行中的容器 `mineru3` 只分配了 GPU 1**（`docker inspect` 显示 `DeviceIDs:["1"]`）。建议启动命令明确指定单卡，避免抢占 GPU 0 上其他业务。

---

## 2. 容器内进程结构

```
mineru3 容器
└── PID 1  /usr/bin/python3 /usr/local/bin/mineru-api --host 0.0.0.0 --port 8000
       │   （FastAPI + 单 uvicorn worker，无 --workers）
       │
       └── PID 325  VLLM::EngineCore  （vLLM v0.21.0 引擎子进程，使用 GPU 1）
```

端口映射：
- `8001 → 8000`：MinerU FastAPI 主服务
- `30000 → 30000`：vLLM 服务端口（由 MinerU 内部 spawn）
- `7860 → 7860`：Gradio 可视化界面
- `8002 → 8002`：预留端口

---

## 3. 并发控制机制（核心）

### 3.1 三层瓶颈链路

```
客户端请求 (任意数量)
     │
     ▼
┌──────────────────────────────────────────────┐
│ MinerU API 层 (PID 1)                         │
│  ├─ asyncio.Queue (无界队列, 24h 任务保留)    │  ← 超过上限的任务在此排队
│  └─ asyncio.Semaphore(N)  ← 硬性闸门 ★       │
│         同一时刻只放行 N 个任务               │
└──────────────────────────────────────────────┘
     │  当前 N = 3
     ▼
┌──────────────────────────────────────────────┐
│ vLLM EngineCore (PID 325, GPU 1)             │
│  模型: MinerU2.5-Pro-2605-1.2B (1.2B VLM)    │
│  max_num_seqs = 256 (vLLM 默认, 未被触及)     │  ← 容量远大于 3
│  gpu_memory_utilization = 0.5 (用了 ~49GB)   │
│  tensor_parallel_size = 1                    │
└──────────────────────────────────────────────┘
```

### 3.2 MinerU API 层信号量（真正的瓶颈）

源码位置：`mineru/cli/fast_api.py`

```python
# 模块级信号量，全局唯一
_request_semaphore: Optional[asyncio.Semaphore] = None
_configured_max_concurrent_requests = 1

def create_app():
    ...
    if is_mac_environment():
        max_concurrent_requests = 1
    else:
        max_concurrent_requests = read_max_concurrent_requests(
            default=DEFAULT_MAX_CONCURRENT_REQUESTS   # = 3
        )
    _configured_max_concurrent_requests = max_concurrent_requests
    _request_semaphore = asyncio.Semaphore(max_concurrent_requests)
    ...

# 每个任务（sync + async）都必须经过信号量
async def _process_task(self, task_id: str) -> None:
    task = self.tasks.get(task_id)
    if task is None:
        return
    try:
        if _request_semaphore is not None:
            async with _request_semaphore:          # ← 最多 N 个能同时进入
                await self._run_task(task)
        ...
```

关键点：**sync `/file_parse` 与 async `/tasks` 共享同一个 `asyncio.Semaphore`**。

- `/tasks`（异步）：提交后立即返回 `task_id`，超过 N 的任务进入 `asyncio.Queue` 排队（队列无界，任务保留 24 小时）。
- `/file_parse`（同步）：本质也是把任务丢进**同一个异步队列**，再通过 `wait_for_terminal_state` 阻塞等待结果。因此同步接口同样受 N 限制。

### 3.3 默认值 3 是硬编码，非硬件推导

源码位置：`mineru/cli/api_protocol.py`

```python
DEFAULT_MAX_CONCURRENT_REQUESTS = 3          # 硬编码默认值
DEFAULT_PROCESSING_WINDOW_SIZE = 64
```

读取逻辑：`mineru/utils/config_reader.py`

```python
def get_max_concurrent_requests(default: int = 3) -> int:
    if default <= 0:
        raise ValueError(...)
    value = os.getenv('MINERU_API_MAX_CONCURRENT_REQUESTS')   # ← 唯一配置入口
    if value is None:
        return default                                        # 不设环境变量 → 用默认 3
    ...
    return max_concurrent_requests
```

**默认值 3 与 GPU 数量、显存大小、vLLM 配置完全无关**，是一个静态常量。当前容器没有设置 `MINERU_API_MAX_CONCURRENT_REQUESTS` 环境变量，因此取默认 3。

### 3.4 三重证据确认

| 证据来源 | 输出 |
|---------|------|
| `/health` 接口 | `"max_concurrent_requests": 3` |
| 容器启动日志 | `Request concurrency limited to 3` |
| 源码常量 | `DEFAULT_MAX_CONCURRENT_REQUESTS = 3` |

---

## 4. vLLM 后端容量（下游未触及的富余）

vLLM EngineCore 启动日志关键参数：

```
model='/root/.cache/modelscope/hub/models/OpenDataLab/MinerU2___5-Pro-2605-1___2B'
dtype=torch.bfloat16
max_seq_len=8192
tensor_parallel_size=1
gpu_memory_utilization=0.5          # → 占 GPU 1 的 ~49GB / 98GB
enable_prefix_caching=True
enable_chunked_prefill=True
cudagraph_capture_sizes=[1,2,4,...,256]   # 说明 vLLM 可批量处理至 256 序列
```

- 模型仅 1.2B 参数，占用显存小；
- `gpu_memory_utilization=0.5` 只用了 GPU 1 的一半显存（49GB / 98GB），还剩约 49GB；
- vLLM 默认 `max_num_seqs=256`，单卡可批量处理大量序列；
- 也就是说，**vLLM 层的容量远大于 MinerU 信号量设置的 3**，下游完全没成为瓶颈。

---

## 5. 瓶颈分层总览

| 层级 | 当前限制 | 是否触顶 | 提升方式 |
|------|---------|---------|---------|
| **MinerU 信号量** | `Semaphore(3)` | ✅ **触顶，这是真正的瓶颈** | 环境变量 `MINERU_API_MAX_CONCURRENT_REQUESTS=N`，重启容器 |
| vLLM `max_num_seqs` | 256（默认） | ❌ 远未触及 | vLLM 启动加 `--max-num-seqs` |
| GPU VRAM | 49GB / 98GB（用了 50%） | ❌ 还剩 ~49GB | 调 `--gpu-memory-utilization` |
| CPU / 内存 / shm | 192 核 / 1TB / 32GB | ❌ 完全不构成限制 | — |

---

## 6. 提升并发的方案

### 6.1 方案 A：调大单容器软限制（最简单，立即生效）

当前硬件（1.2B 小模型 + 49GB 空闲显存 + vLLM 默认 max_num_seqs=256）完全有能力支撑远超 3 的并发。只需在启动命令加一个环境变量：

```bash
docker run --gpus all \
  -e MINERU_API_MAX_CONCURRENT_REQUESTS=8 \
  --shm-size 32g \
  -p 30000:30000 -p 7860:7860 -p 8001:8000 -p 8002:8002 \
  --ipc=host \
  -v /data/zengqiang/mineru-workspace/:/vllm-workspace/output \
  -d \
  mineru:latest \
  mineru-api --host 0.0.0.0 --port 8000
```

- **保守建议取 8–16**。1.2B 模型 + 49GB 空闲显存足以支撑。
- 取再高（如 32+）需要同步调大 vLLM 的 `--max-num-seqs` 并密切监控显存与吞吐。
- 验证方式：启动后访问 `http://10.147.254.44:8001/health`，确认 `max_concurrent_requests` 字段已变为新值。

### 6.2 方案 B：用满 6 张空闲 GPU（线性扩容）

单容器只能用 1 张 GPU（vLLM `tensor_parallel_size=1`）。服务器有 6 张空闲 GPU（GPU 2–7），可每卡起一个容器，前置负载均衡：

```bash
# 每张空闲 GPU 起一个独立 MinerU 容器
for i in 2 3 4 5 6 7; do
  docker run --gpus "\"device=${i}\"" \
    -e MINERU_API_MAX_CONCURRENT_REQUESTS=8 \
    --shm-size 16g \
    -p $((8000+i)):8000 -p $((30000+i-2)):30000 \
    --ipc=host \
    -v /data/zengqiang/mineru-workspace-${i}/:/vllm-workspace/output \
    -d \
    --name mineru-gpu${i} \
    mineru:latest \
    mineru-api --host 0.0.0.0 --port 8000
done
```

前置 Nginx / HAProxy 把请求轮询到 `8002~8007`。6 卡 × 8 并发 = **理论 48 并发**。

> 注意：每个容器需要独立的 `output` 挂载目录，否则多容器写入会冲突。

### 6.3 方案 C：单容器 vLLM 多卡张量并行（不推荐）

把 vLLM 改成 `tensor_parallel_size=N` 占多卡。但 MinerU 的 vLLM 是其内部 spawn 的子进程，改 TP 需要侵入式修改启动参数；且 1.2B 小模型多卡并行通信开销不划算，加速比远低于线性。**方案 B 更优**。

---

## 7. 量化参考

> ⚠️ 以下为基于参数的推算，实际并发性能受文件类型、页数、`effort`、`parse_method` 影响很大，建议以压测为准。

| 配置 | 理论并发 | 显存占用 | 适用场景 |
|------|---------|---------|---------|
| 默认（当前） | 3 | 49GB / 98GB（单卡） | 现状，无需改动 |
| 方案 A `=8` | 8 | ~55GB / 98GB（单卡） | 单容器轻度扩容，推荐起步值 |
| 方案 A `=16` | 16 | ~70GB / 98GB（单卡，估算） | 单容器重度扩容，需监控显存 |
| 方案 B 6 卡 × 8 | 48 | 6 卡各 ~55GB | 充分利用闲置硬件，需运维 |

---

## 8. 操作建议清单

1. **立即生效**：重启容器时增加 `-e MINERU_API_MAX_CONCURRENT_REQUESTS=8`。
2. **修正文档偏差**：启动命令建议显式指定 GPU（如 `--gpus '"device=1"'`），避免 `--gpus all` 抢占 GPU 0 上其他业务。详见 [mineru使用说明.md §1](./mineru使用说明.md)。
3. **若并发需求 > 16**：采用方案 B 多容器 + 负载均衡，用满 6 张空闲 GPU。
4. **压测验证**：改完后用 `scripts/test_mineru_api.py` 并发提交任务，观察 `/health` 的 `processing_tasks` 是否达到上限、是否 OOM、吞吐是否线性提升。

---

## 9. 相关脚本

- `scripts/test_mineru_api.py`：MinerU API 直连测试脚本，支持同步/异步调用、ZIP 下载、JSON 保存，可用于压测验证。
