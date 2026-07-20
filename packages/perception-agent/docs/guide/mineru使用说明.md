# MinerU API 接口使用说明

> 服务地址：`http://10.147.254.44:8001`
> 文档地址：`http://10.147.254.44:8001/docs`
> 基于 FastAPI / OpenAPI 3.1.0（响应 schema 未严格定义，字段以实际返回为准）

---

## 1. 服务部署信息

使用如下 Docker 命令启动服务：

```bash
docker run -d \
  --name mineru \
  --gpus '"device=1"' \
  -e MINERU_API_MAX_CONCURRENT_REQUESTS=8 \
  --shm-size 32g \
  -p 30000:30000 -p 7860:7860 -p 8001:8000 -p 8002:8002 \
  --ipc=host \
  -v /data/zengqiang/mineru-workspace/:/vllm-workspace/output \
  mineru:latest \
  mineru-api --host 0.0.0.0 --port 8000
```

说明：
- 容器内部服务监听 `8000` 端口；外部通过 `8001` 端口访问。
- `--gpus '"device=1"'` 把容器钉到物理 GPU 1（空闲卡）。**不要用 `--gpus all`**：vLLM 默认占用 `cuda:0`，若 GPU 0 被其他进程（如本机的 `sglang`）占用，vlm-engine/hybrid-engine 会因显存不足初始化失败。用 `nvidia-smi` 查空闲卡编号替换 `1`。详见 [常见问题 §6](#6-vlmengine--hybridengine-报-engine-core-initialization-failed)。
- `-e MINERU_API_MAX_CONCURRENT_REQUESTS=8` 设置**并发解析任务上限**。MinerU 默认值为 `3`（源码硬编码，与硬件无关），即便服务器有 8 张 H20 也只能同时跑 3 个任务，其余排队。本机 H20 + 1.2B VLM 模型可轻松支撑 8–16 并发，建议设为 `8`。完整瓶颈分析与扩容方案见 [mineru并发量分析.md](./mineru并发量分析.md)。
- `--shm-size 32g` 为共享内存分配 32GB，避免大文件处理时 OOM。
- `-v /data/zengqiang/mineru-workspace/:/vllm-workspace/output`：将容器内的解析输出目录挂载到宿主机，解析结果（Markdown、图片等）可直接在宿主机访问，容器重启后不丢失。

> 验证并发配置：启动后访问 `http://10.147.254.44:8001/health`，响应中的 `max_concurrent_requests` 字段应反映所设值（默认 3，本例设为 8）。

---

## 1.1 输出文件持久化

MinerU 解析结果默认保存在容器内 `/vllm-workspace/output/`，通过 `-v` 挂载后可在宿主机直接访问。

### 输出目录结构

```
宿主机 /data/zengqiang/mineru-workspace/
└── <task_id>/
    ├── uploads/                          # 原始上传文件
    │   └── <filename>.pdf
    └── <filename>/
        └── txt/
            ├── <filename>.md             # ← 解析结果 Markdown
            └── images/                   # ← 提取的图片
```

- 每个解析任务按 `task_id` 生成独立子目录。
- Markdown 文件可直接在宿主机上读取、编辑、拷贝。
- 容器重启后历史结果依然保留（因挂载在宿主机上）。

---

## 2. 接口概览

MinerU 共暴露 5 个 HTTP 接口，覆盖健康检查、同步解析、异步解析三种工作模式：

| 方法 | 路径 | Operation ID | 说明 |
|------|------|--------------|------|
| GET | `/health` | `health_check_health_get` | 健康检查 |
| POST | `/file_parse` | `parse_pdf_file_parse_post` | 同步解析文件（阻塞等待结果，HTTP 200） |
| POST | `/tasks` | `submit_parse_task_tasks_post` | 提交异步解析任务（立即返回 `task_id`，HTTP 202） |
| GET | `/tasks/{task_id}` | `get_async_task_status_tasks__task_id__get` | 查询异步任务状态 |
| GET | `/tasks/{task_id}/result` | `get_async_task_result_tasks__task_id__result_get` | 获取异步任务结果 |

**何时用同步 vs 异步**：
- 小文件、希望立即拿到结果 → `/file_parse`（同步阻塞）
- 大文件、超时敏感、需批量提交 → `/tasks`（异步 + 轮询）
- 同步接口可能因文件过大而超时，生产环境建议优先使用异步接口。

---

## 3. 通用请求参数

`/file_parse` 与 `/tasks` 共享相同的请求体 schema（`multipart/form-data`），仅 `files` 必填，其余均可选。下表为完整参数清单，按用途分组。

### 3.1 文件输入

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `files` | `array[binary]` | ✅ | — | 上传文件，支持 PDF、图片、DOCX、PPTX、XLSX，可一次上传多个 |

### 3.2 解析后端 `backend`（默认 `hybrid-engine`）

| 取值 | 计算位置 | 语言支持 | 说明 |
|------|----------|----------|------|
| `pipeline` | CPU | 多语言 | 通用、无幻觉，走 PaddleOCR |
| `vlm-engine` | 本地 GPU | 仅中英文 | 高精度，依赖本地 vLLM |
| `vlm-http-client` | 远程 GPU | 仅中英文 | 高精度，调用 OpenAI 兼容远程服务 |
| `hybrid-engine` | 本地 GPU | 多语言 | 混合引擎，默认。用 `effort` 切换 medium/high |
| `hybrid-http-client` | 远程 GPU | 多语言 | 远程混合引擎，仍需少量本地算力，用 `effort` 切换 medium/high |

### 3.3 `effort`（默认 `medium`，仅 `hybrid` 系列后端有效）

| 取值 | 行为 |
|------|------|
| `medium` | 速度优先，**自动关闭**图片/图表分析，平衡精度与效率 |
| `high` | 精度优先，**支持**图片/图表分析，耗时更长 |

### 3.4 `parse_method`（默认 `auto`，仅 `pipeline` / `hybrid` 后端有效）

| 取值 | 行为 |
|------|------|
| `auto` | 根据文件类型自动选择 txt 或 ocr |
| `txt` | 文本提取模式（适合可复制文本的 PDF） |
| `ocr` | OCR 模式（适合扫描件、图片型 PDF） |

### 3.5 `server_url`（仅 `vlm-http-client` / `hybrid-http-client` 后端有效）

- 类型：`string | null`，默认 `null`
- 用途：指定 OpenAI 兼容服务的 URL，例如 `http://127.0.0.1:30000`
- 未指定时，http-client 后端将无法正确路由到远程推理服务，需显式传入。

### 3.6 语言列表 `lang_list`（默认 `["ch"]`，仅 `pipeline` 后端有效）

输入文档语言用于提升 OCR 精度，可选值：

| 值 | 支持语言 |
|----|----------|
| `ch` / `ch_server` | 中、英、日、繁体中文、拉丁 |
| `korean` | 韩、英 |
| `ta` | 泰米尔、英 |
| `te` | 泰卢固、英 |
| `ka` | 卡纳达 |
| `th` | 泰、英 |
| `el` | 希腊、英 |
| `arabic` | 阿拉伯、波斯、维吾尔、乌尔都、普什图、库尔德、信德、俾路支、英 |
| `east_slavic` | 俄、白俄、乌克兰、英 |
| `cyrillic` | 俄、白俄、乌克兰、塞尔维亚(西里尔)、保加利亚、蒙古、哈萨克、吉尔吉斯、塔吉克、马其顿、鞑靼等 + 英 |
| `devanagari` | 印地、马拉地、尼泊尔、比哈尔、迈蒂利、梵语、 konkani 等 + 英 |

### 3.7 功能开关

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `formula_enable` | bool | `true` | 启用公式解析 |
| `table_enable` | bool | `true` | 启用表格解析 |
| `image_analysis` | bool | `true` | 启用图片/图表分析（VLM 与 hybrid 后端；hybrid medium 会自动关闭） |

### 3.8 返回内容控制

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `return_md` | bool | `true` | 返回 Markdown 内容 |
| `return_middle_json` | bool | `false` | 返回中间 JSON |
| `return_model_output` | bool | `false` | 返回模型原始输出 JSON |
| `return_content_list` | bool | `false` | 返回 content_list JSON（版面元素列表） |
| `return_images` | bool | `false` | 返回提取的图片 |
| `response_format_zip` | bool | `false` | 以 ZIP 格式返回结果（替代 JSON） |
| `return_original_file` | bool | `false` | 在 ZIP 中保留原始输入文件；**仅在 `response_format_zip=true` 时生效** |
| `client_side_output_generation` | bool | `false` | 由客户端生成最终 markdown/content_list；服务端只返回中间 JSON、模型输出、图片 |

### 3.9 页码范围

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `start_page_id` | int | `0` | PDF 解析起始页（从 0 开始） |
| `end_page_id` | int | `99999` | PDF 解析结束页（从 0 开始） |

> 显存紧张时，调小 `end_page_id - start_page_id` 范围可降低 OOM 风险。

---

## 4. 接口详情

### 4.1 健康检查 `GET /health`

无参数。用于探活、负载均衡健康探测。

```bash
curl -s http://10.147.254.44:8001/health
```

响应示例：

```json
{ "status": "ok" }
```

---

### 4.2 同步解析 `POST /file_parse`

**功能**：上传文件 → 服务端阻塞解析 → 同一响应中返回最终结果。

**适用场景**：小文件、希望立即拿到结果、客户端不便做轮询的场景。

**请求**（`multipart/form-data`）：

```bash
curl -X POST "http://10.147.254.44:8001/file_parse" \
  -F "files=@/path/to/Sany-magazine-crane-202103-EN.pdf" \
  -F "backend=hybrid-engine" \
  -F "effort=high" \
  -F "parse_method=auto" \
  -F "lang_list=ch" \
  -F "return_md=true" \
  -F "return_content_list=true"
```

**响应**：HTTP 200，JSON 中包含解析结果（字段见 §5）。
**错误**：HTTP 422 表示参数校验失败（如未传 `files`）。

> 大文件使用同步接口可能因网关/反代超时被切断，建议切到异步接口。

---

### 4.3 异步提交 `POST /tasks`

**功能**：上传文件 → 立即返回 `task_id` → 客户端轮询状态/结果。

**适用场景**：大文件、批量提交、超时敏感、需要解耦提交与获取结果的场景。

**提交任务**：

```bash
curl -X POST "http://10.147.254.44:8001/tasks" \
  -F "files=@/path/to/Sany-magazine-crane-202103-EN.pdf" \
  -F "backend=hybrid-engine" \
  -F "effort=high" \
  -F "return_md=true"
```

**响应**：HTTP 202，返回 `task_id`：

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

---

### 4.4 查询任务状态 `GET /tasks/{task_id}`

**路径参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | ✅ | 异步提交时返回的任务 ID |

```bash
curl -s "http://10.147.254.44:8001/tasks/550e8400-e29b-41d4-a716-446655440000"
```

**典型状态**：`pending` → `processing` → `done` / `failed`（字段名以实际返回为准）。

---

### 4.5 获取任务结果 `GET /tasks/{task_id}/result`

**路径参数**：同 §4.4。

```bash
curl -s "http://10.147.254.44:8001/tasks/550e8400-e29b-41d4-a716-446655440000/result"
```

任务完成时返回与 `/file_parse` 同结构的解析结果；未完成或失败时返回相应状态/错误信息。

---

## 5. 返回结构说明

> ⚠️ OpenAPI 规范中成功响应 schema 为空对象 `{}`，未严格定义字段，**以下为根据参数语义推断的字段名，以实际返回为准**。建议先用 `/file_parse` 测试一次并打印响应键。

成功时，JSON 中通常包含：

| 字段（推断） | 对应请求参数 | 说明 |
|--------------|--------------|------|
| `md` / `markdown` | `return_md=true` | 解析后的 Markdown 文本 |
| `content_list` | `return_content_list=true` | 版面元素列表（段落、表格、图片等） |
| `middle_json` | `return_middle_json=true` | 中间处理结果 |
| `model_output` | `return_model_output=true` | 模型原始输出 |
| `images` | `return_images=true` | 提取的图片（base64 或 URL） |

当 `response_format_zip=true` 时，响应体为 ZIP 文件流，上述内容打包在 ZIP 内；`return_original_file=true` 还会把原始上传文件一起打包。

当 `client_side_output_generation=true` 时，服务端只返回中间数据（middle JSON + model output + images），由客户端自行生成最终 markdown / content_list，适合前端做二次定制。

---

## 6. 常见问题

1. **端口映射**：外部访问使用 `8001`，容器内服务运行在 `8000`。
2. **大文件超时**：同步接口可能因文件过大而超时，建议使用 `/tasks` 异步接口。
3. **GPU 显存不足**：调小 `end_page_id - start_page_id` 范围，或降低 `effort`（high → medium）。
4. **中英文混合文档**：使用 `hybrid-engine` + `lang_list=["ch"]` 通常效果最佳。
5. **扫描件/图片 PDF**：设置 `parse_method=ocr`。
6. **http-client 后端连接失败**：检查 `server_url` 是否已正确填写（指向 OpenAI 兼容服务，如 `http://127.0.0.1:30000`）。
7. **并发量低 / 任务一直排队**：MinerU 默认只允许 **3 个并发**解析任务（源码硬编码 `DEFAULT_MAX_CONCURRENT_REQUESTS = 3`，与 GPU 数量、显存无关），超过的任务进队列等待。通过 `-e MINERU_API_MAX_CONCURRENT_REQUESTS=8` 提升上限。用 `GET /health` 的 `max_concurrent_requests` 字段验证。完整瓶颈分析与扩容方案见 [mineru并发量分析.md](./mineru并发量分析.md)。

### 6.1 vlm-engine / hybrid-engine 报 `Engine core initialization failed`

<a name="6-vlmengine--hybridengine-报-engine-core-initialization-failed"></a>

**现象**：调用 `vlm-engine` 或 `hybrid-engine` 后端时任务失败，API 返回：

```
Engine core initialization failed. See root cause above. Failed core proc(s): {}
```

而 `pipeline` 后端正常（纯 CPU，走 PaddleOCR，不碰 GPU）。

**根因**：vLLM 引擎默认使用 `cuda:0`（物理 GPU 0）。若 GPU 0 已被其他进程占用（如本机 `sglang` 服务占用约 83GB / 97GB），vLLM 申请默认显存（`gpu_memory_utilization=0.5`，约 47GB）时剩余显存不足，引擎核心子进程初始化失败。API 返回的只是汇总错误，**真正的根因在容器日志里**：

```
ValueError: Free memory on device cuda:0 (13.15/95.07 GiB) on startup is less than
desired GPU memory utilization (0.5, 47.54 GiB). Decrease GPU memory utilization
or reduce GPU memory used by other processes.
```

崩溃路径：MinerU `vlm_analyze.py` → vLLM `gpu_worker.py init_device()` → `request_memory()` 抛 ValueError → 子进程崩 → `wait_for_engine_startup()` 抛 RuntimeError → MinerU 透传。`hybrid-engine` 复用同一 ModelSingleton，所以 vlm 挂则 hybrid 必挂。

**定位步骤**：

```bash
# 1. 看哪张 GPU 被占（找 memory.used 很高、memory.free 很低的卡）
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader

# 2. 看容器真实崩溃原因（关键：找 "Free memory on device" 行）
docker logs <容器名> 2>&1 | grep -A2 "Free memory on device"

# 3. 看容器里能看到哪些 GPU
docker exec <容器名> nvidia-smi -L
```

**修复**：把容器钉到一张空闲 GPU。**必须用 `--gpus '"device=N'"`，不能用 `--gpus all -e NVIDIA_VISIBLE_DEVICES=N`**——`--gpus all` 标志优先级高于 `NVIDIA_VISIBLE_DEVICES` 环境变量，容器仍能看到全部 GPU，vLLM 仍会抢 `cuda:0`：

```bash
# 停掉旧容器
docker stop <旧容器名> && docker rm <旧容器名>

# 用空闲的 GPU 1 重建（注意 --gpus 的引号写法）
docker run -d --name mineru \
  --gpus '"device=1"' \
  -e MINERU_API_MAX_CONCURRENT_REQUESTS=8 \
  --shm-size 32g \
  -p 30000:30000 -p 7860:7860 -p 8001:8000 -p 8002:8002 \
  --ipc=host \
  -v /data/zengqiang/mineru-workspace/:/vllm-workspace/output \
  mineru:latest \
  mineru-api --host 0.0.0.0 --port 8000

# 验证：容器里应该只看到 1 张 GPU（物理 GPU 1 被重映射为 cuda:0）
docker exec mineru nvidia-smi -L
```

**关键点**：`--gpus all` 让容器看到所有 GPU，vLLM 默认选 `cuda:0`；只有 `--gpus '"device=N'"` 才能把指定物理 GPU 钉成容器内的 `cuda:0`，vLLM 才会用那张（空闲）卡。选哪张 `N` 用 `nvidia-smi` 查空闲卡编号。

---

## 7. 相关脚本

- `scripts/test_mineru_api.py`：本仓库提供的 MinerU API 直连测试脚本，支持同步/异步调用、ZIP 下载、JSON 保存。
