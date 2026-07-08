---
kind: dependency_management
name: 基于 uv workspace 的多包依赖管理
category: dependency_management
scope:
    - '**'
source_files:
    - pyproject.toml
    - uv.lock
    - .python-version
    - .pre-commit-config.yaml
    - ruff.toml
    - packages/agent-core/pyproject.toml
    - packages/agent-rl/pyproject.toml
    - packages/companion-agent/pyproject.toml
    - packages/quant-agent/pyproject.toml
---

## 系统概览
本项目采用 **uv** 作为 Python 包管理器与虚拟环境工具，通过 `pyproject.toml` 声明一个多包工作区（workspace），聚合 `packages/agent-core`、`agent-rl`、`quant-agent`、`companion-agent` 四个子包，并由根 `main.py` 统一编排启动。所有第三方依赖的版本锁定由根目录的 `uv.lock` 统一管理。

## 关键文件与职责
- `pyproject.toml`：工作区根配置，声明 `requires-python = ">=3.12"`、workspace members (`packages/*`)、顶层依赖（仅引用四个子包名）以及 `dependency-groups.dev`（pre-commit、ruff）。
- `uv.lock`：全局锁文件，记录解析后的完整依赖树、各包的来源（含阿里云镜像 `mirrors.cloud.aliyuncs.com/pypi/simple`）、hash 校验值，并列出 manifest 中的全部成员包。当前锁定 Python 版本为 `==3.13.*`。
- `packages/*/pyproject.toml`：各子包独立元数据，均使用 `build-backend = "uv_build"`，要求 `uv_build>=0.11.6,<0.12.0`；当前子包自身 `dependencies` 为空，运行时依赖集中在被引用的外部包（如 agentpool）中。
- `.python-version`：配合 uv 指定项目 Python 版本。
- `.pre-commit-config.yaml` + `ruff.toml`：开发期依赖（lint、格式化）通过 dependency-groups 管理，不进入运行期。

## 架构与约定
1. **Workspace 聚合**：根 `pyproject.toml` 通过 `[tool.uv.workspace].members = ["packages/*"]` 自动发现子包，并通过 `[tool.uv.sources]` 将顶层依赖名映射到本地 workspace 包，避免在子包间重复声明依赖。
2. **单锁文件策略**：所有依赖解析结果收敛到根 `uv.lock`，确保多包共享一致的第三方依赖版本，避免子包各自锁定导致冲突。
3. **私有镜像源**：`uv.lock` 中所有包来源指向阿里云 PyPI 镜像，表明团队已配置 uv 的全局或项目级 index URL，用于加速下载与内网访问。
4. **构建后端统一**：所有子包使用 `uv_build` 作为 PEP 517 构建后端，版本约束 `>=0.11.6,<0.12.0`，保证构建一致性。
5. **脚本入口**：每个子包通过 `[project.scripts]` 暴露 CLI 命令（如 `agent-core`、`agent-rl`、`quant-agent`、`companion-agent`），由 uv 在安装时注册。

## 开发者应遵循的规则
- **新增依赖**：在对应子包的 `pyproject.toml` 的 `dependencies` 中声明，或在根 `pyproject.toml` 的顶层依赖中添加（若为全工作区共享）。随后执行 `uv lock` 更新 `uv.lock`。
- **不要手动编辑 `uv.lock`**：该文件由 uv 自动生成，手动修改会导致不一致。
- **保持 Python 版本一致**：根配置要求 `>=3.12`，锁文件锁定 `==3.13.*`，新成员需使用相同 Python 版本。
- **开发依赖隔离**：使用 `[dependency-groups]` 管理 dev 依赖（pre-commit、ruff），避免污染运行环境。
- **子包间依赖**：通过 workspace source 机制引用其他子包，无需在子包 pyproject 中写绝对路径或版本号。
- **镜像源配置**：如需切换或新增私有索引，应在 uv 全局配置或项目级 `uv.toml` 中设置，而非直接改 `uv.lock`。