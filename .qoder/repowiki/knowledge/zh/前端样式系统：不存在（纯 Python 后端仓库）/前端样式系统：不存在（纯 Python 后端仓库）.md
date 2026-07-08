---
kind: frontend_style
name: 前端样式系统：不存在（纯 Python 后端仓库）
category: frontend_style
scope:
    - '**'
---

经全面扫描，该仓库为纯 Python 多包工作区（uv workspace），包含 agent-core、agent-rl、quant-agent、companion-agent 四个子包，以及 .agent/skills 下的 Agent 技能脚本。仓库中未发现任何前端样式相关代码或配置：

- 无 `*.css` / `*.scss` / `*.sass` / `*.less` / `*.stylus` 文件
- 无 `tailwind.config.*`、`postcss.config.*`、`vite.config.*`、`webpack.config.*` 等构建/样式工具配置
- 无 `package.json`、`tsconfig.json` 等前端工程化清单
- 所有 packages 均为 Python 包（含 `pyproject.toml` + `src/` 结构）
- 仅 `.agent/skills` 下存在少量 HTML 模板（如 `templates/viewer.html`、`templates/result-card.html`），用于 Skill 生成算法艺术或截图卡片，但这些是静态模板而非项目 UI 样式体系

因此本仓库不涉及前端样式系统，`frontend_style` 类别不适用。