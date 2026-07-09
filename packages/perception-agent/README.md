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
