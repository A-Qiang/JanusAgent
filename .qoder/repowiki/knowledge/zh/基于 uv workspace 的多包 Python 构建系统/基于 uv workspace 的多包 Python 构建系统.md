---
kind: build_system
name: 基于 uv workspace 的多包 Python 构建系统
category: build_system
scope:
    - '**'
source_files:
    - pyproject.toml
    - main.py
    - .pre-commit-config.yaml
    - ruff.toml
    - .python-version
    - packages/agent-core/pyproject.toml
    - packages/agent-rl/pyproject.toml
---

## 构建系统与工具链概览

JanusAgent 采用 **uv** 作为统一的依赖管理与构建工具，通过 PEP 621 `pyproject.toml` 声明式配置，组织为多包工作区（workspace）结构。项目未使用 Makefile、Dockerfile、CI 流水线或传统 setup.py，完全依赖 uv 生态完成开发、构建与分发。

### 核心架构：Workspace + 子包

- **根级 `pyproject.toml`** 声明 workspace 成员 `packages/*`，并通过 `[dependency-groups]` 管理开发期依赖（pre-commit、ruff），通过 `[tool.uv.sources]` 将四个子包解析为本地 workspace 源，实现零拷贝的跨包引用。
- **四个子包** `agent-core`、`agent-rl`、`quant-agent`、`companion-agent` 各自拥有独立 `pyproject.toml`，统一使用 `uv_build>=0.11.6,<0.12.0` 作为 build-backend，遵循 PEP 517/621 标准。
- **入口编排**：根目录 `main.py` 直接 import 各子包的顶层模块并调用其 `hello()` / `main()`，作为整个应用的统一启动点。

### 代码质量与预提交钩子

- **Ruff** 作为唯一 lint/format 工具，在 `ruff.toml` 中集中配置规则集（覆盖 A/B/C4/COM/E/ERA/F/FLY/G/I/ICN/ISC/LOG/PERF/PIE/PLC/PLE/PLW/PT/PTH/RET/RUF/S/SIM/T/TRY/UP/W 等），target-version 锁定 py312，行宽 180。
- **pre-commit** 集成两个 astral-sh 官方 hook：`uv-lock`（保证 lock 文件同步）、`ruff-check --fix` + `ruff-format`（自动修复与格式化）。
- `.python-version` 约束全局 Python 版本。

### 构建与安装流程

| 操作 | 命令 | 说明 |
|---|---|---|
| 安装工作区 | `uv sync` | 根据 `uv.lock` 安装所有子包及 dev 依赖组 |
| 运行应用 | `uv run main.py` | 通过 workspace entrypoint 执行根入口 |
| 构建分发包 | `uv build` | 对每个子包生成 sdist/wheel（由 uv_build 驱动） |
| 发布到 PyPI | `uv publish -p <token>` | 逐个子包发布（无自动化脚本） |

### 设计决策与约定

1. **纯声明式构建**：不维护 Makefile / shell 脚本 / tox / nox，所有构建逻辑集中在 `pyproject.toml`，降低心智负担。
2. **子包最小化依赖**：各子包 `dependencies = []`，仅通过 workspace 引用共享依赖，避免重复锁定。
3. **脚本入口标准化**：每个子包通过 `[project.scripts]` 暴露 CLI 命令（如 `agent-core`、`agent-rl`），但当前仅用于演示。
4. **无测试框架集成**：未发现 pytest/unittest 配置或测试目录，测试尚未纳入构建流程。
5. **无容器化/CI**：仓库内仅有 `docs/docker/docker-basics.md` 入门文档，不存在 Dockerfile、docker-compose 或 GitHub Actions 配置，部署流程未自动化。

### 开发者应遵循的规则

- 新增子包时，在根 `pyproject.toml` 的 `[tool.uv.workspace].members` 和 `[dependency-groups]` 中注册，并在子包 `pyproject.toml` 中设置 `build-system.requires = ["uv_build>=0.11.6,<0.12.0"]`。
- 所有 Python 代码必须通过 `ruff check --fix && ruff format`，并提交前由 pre-commit 自动校验。
- 依赖变更需运行 `uv lock` 更新锁文件，pre-commit 会强制检查一致性。
- 如需扩展构建流程（添加测试、打包、发布），建议优先复用 uv 原生能力而非引入 Makefile 或 tox。