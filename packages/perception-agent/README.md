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
