# 模型下载脚本使用说明

## 概述

`download_model.py` 是一个从 [ModelScope](https://modelscope.cn) 下载模型的工具脚本，
支持断点续传、文件过滤、多版本选择等功能。

## 环境要求

- **Python** >= 3.8
- **操作系统**：Linux / macOS / Windows

> **提示**：首次运行时会自动安装 `modelscope` Python 包依赖。

---

## 快速开始

### 下载 MinerU2.5-Pro-2605-1.2B 模型

```bash
cd /home/zengqiang/projects/JanusAgent
python scripts/download_model.py
```

脚本会将模型下载到 `/home/zengqiang/models/MinerU2.5-Pro-2605-1.2B/` 目录下。

### 命令行验证下载结果

```bash
ls -lh /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B/
```

---

## 完整参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--model` | str | `OpenDataLab/MinerU2.5-Pro-2605-1.2B` | ModelScope 模型 ID（格式：`组织/模型名`） |
| `--local-dir` | str | `/home/zengqiang/models/MinerU2.5-Pro-2605-1.2B` | 模型下载后的本地保存路径 |
| `--revision` | str | 无（默认 master） | 模型版本号或 Git 分支名 |
| `--ignore-patterns` | list[str] | 无 | 要跳过的文件模式（支持通配符） |
| `--allow-patterns` | list[str] | 无 | 仅下载匹配的文件模式 |
| `--token` | str | 无 | ModelScope 个人访问令牌（私有模型必填） |
| `--quiet` | flag | false | 静默模式，减少输出信息 |
| `--help` | flag | - | 显示帮助信息 |

---

## 使用场景

### 1. 下载其他模型

```bash
python scripts/download_model.py \
    --model Qwen/Qwen2.5-7B-Instruct \
    --local-dir /home/zengqiang/models/Qwen2.5-7B-Instruct
```

### 2. 下载特定版本的模型

```bash
python scripts/download_model.py \
    --model OpenDataLab/MinerU2.5-Pro-2605-1.2B \
    --revision v1.0
```

### 3. 仅下载部分文件（跳过 safetensors 权重）

```bash
python scripts/download_model.py \
    --ignore-patterns '*.safetensors' '*.bin'
```

### 4. 只下载配置文件或分词器

```bash
python scripts/download_model.py \
    --allow-patterns '*.json' 'tokenizer*' '*.py'
```

### 5. 下载私有模型

```bash
python scripts/download_model.py \
    --model username/private-model \
    --token YOUR_MODELSCOPE_TOKEN
```

> Token 可以从 [ModelScope 个人中心](https://modelscope.cn/my/myaccesstoken) 获取。

---

## 网络与代理

如果遇到网络连接问题，可通过设置环境变量配置代理：

```bash
# HTTP 代理
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

# 然后运行下载
python scripts/download_model.py
```

或者指定 ModelScope 镜像端点：

```bash
# 使用国内镜像
export MODELSCOPE_ENDPOINT=https://modelscope.cn
python scripts/download_model.py
```

---

## 常见问题

### Q: 下载中断后需要重新下载吗？

不需要。`snapshot_download` 支持断点续传——重复执行相同的命令会跳过已下载的文件，
只下载缺失的部分。

### Q: 如何确认下载的文件是否完整？

对比本地文件和远端 `SHA256`，或直接运行模型推理来验证。ModelScope 会自动校验文件完整性。

### Q: 磁盘空间不够怎么办？

- 使用 `--ignore-patterns` 跳过不需要的大文件（如 `*.safetensors`）
- 修改 `--local-dir` 指向磁盘空间更大的路径
- 删除目录下的缓存文件（默认不会缓存中间文件）

---

## 技术细节

脚本底层使用了 ModelScope Python SDK 提供的 [`snapshot_download`](https://www.modelscope.cn/docs/API/snapshot_download)
接口，其工作原理如下：

1. **解析模型 ID** —— 将 `organization/model-name` 映射到远端仓库
2. **获取文件列表** —— 列出仓库中所有需要下载的文件
3. **并发下载** —— 多线程并行拉取文件，自动处理重试和校验
4. **写入本地** —— 按照仓库结构写入 `local_dir`

该接口会自动跳过已存在的且校验通过的文件，从而实现断点续传。
