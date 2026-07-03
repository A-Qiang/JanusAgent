---
name: project-docs-to-html
description: Convert project management Markdown docs (roadmap, todolist, milestone plans) into a highly visual, interactive single-file HTML page with dark/light theme toggle, task status switching with local persistence, status/priority filtering, progress statistics, milestone timeline view, and Markdown export / print. Use when the user asks to visualize, render, or turn a roadmap.md / todolist.md / plan.md into an interactive HTML page, or mentions 可视化/交互 for project planning docs.
---

# 项目文档转交互式 HTML

将 `roadmap.md`、`todolist.md`、里程碑排期等项目管理 Markdown 文档，转化为**单文件、可交互、深浅色可切换**的 HTML 可视化页面。

## 核心原则

- **模板驱动，低自由度**：始终复用 [template.html](template.html) 的结构、CSS、JS，**只替换数据区**（`META` 与 `DATA`）。不要自己从零写样式/脚本，保证团队文档 UI 一致。
- **单文件产物**：无外部依赖，双击即可在浏览器打开。
- **数据与展示分离**：把 md 内容解析成 `DATA` 数组，展示逻辑交给模板。

## 工作流

复制此清单跟踪进度：

```
- [ ] 步骤1：读取源 Markdown（roadmap.md / todolist.md 等）
- [ ] 步骤2：读取 template.html 作为唯一模板
- [ ] 步骤3：解析 md 章节 → 填充 META 与 DATA
- [ ] 步骤4：写出目标 .html（与源 md 同目录，同名不同后缀）
- [ ] 步骤5：自检 DATA 结构与 storageKey 唯一性
```

### 步骤1-2：读取源文件与模板
- 用 Read 读取用户指定的 md 文档。
- 用 Read 读取本 skill 目录下的 `template.html`，作为生成基准。

### 步骤3：解析 md → 填充数据区
将 md 结构映射为 `META` 和 `DATA`（详见下文数据模型）。**只改数据区两个常量，其余代码原样保留**。

### 步骤4：写出 HTML
- 输出路径：默认与源 md **同目录**，文件名同名（如 `todolist.md` → `todolist.html`）。
- 用完整的 template.html 内容作为基底，替换数据区后写入目标路径。

### 步骤5：自检
- `DATA` 中每个任务都有 `p`（P0/P1/P2）与 `t`；有状态的任务带 `status`。
- `META.storageKey` 每个文档唯一（避免多份 HTML 共享 localStorage 冲突），如 `janus_todolist_v1`。
- 时间轴章节用 `type:"timeline"` + `milestones`。

## 数据模型

```js
const META = {
  title: "文档标题",          // 页面 <h1> 与 <title>
  subtitle: "一句话说明",      // 副标题（可选）
  storageKey: "文档唯一键_v1"  // localStorage 命名空间，必须唯一
};

const DATA = [
  // A) 任务清单章节（todolist 类）
  {
    title: "章节标题（可含 emoji）",
    type: "tasks",
    note: "章节说明（可选）",
    tasks: [
      { p: "P0", status: "todo",  t: "任务文本，可用 <strong>强调</strong>" }
    ],
    subs: [                                   // 子分组（可选，如 M0/M2）
      { title: "子分组标题", tasks: [ { p:"P1", status:"doing", t:"..." } ] }
    ]
  },
  // B) 里程碑时间轴章节（roadmap 类）
  {
    title: "路线图章节",
    type: "timeline",
    milestones: [
      { tag:"M0", when:"第 1 月", title:"骨架跑通", desc:"最小闭环", status:"done" }
    ]
  }
];
```

## Markdown → 数据 映射规则

| Markdown 元素 | 映射目标 |
|---|---|
| `# 一级标题` | `META.title` |
| 紧随的 `> 引用` | `META.subtitle` |
| `## 二级标题` | 一个 `DATA` 章节的 `title` |
| `### 三级标题` | 该章节 `subs[].title` |
| `- [ ] / [~] / [x] / [!]` | 任务 `status`：待办/进行中/完成/阻塞 |
| `` `P0` `` `` `P1` `` `` `P2` `` | 任务 `p` |
| `**加粗**` | 转成 `<strong>...</strong>` |
| 里程碑/时间轴类章节（含 M0/M1、月份、阶段） | `type:"timeline"` + `milestones` |

**状态标记对照**（与产物导出保持一致）：
`[ ]`→todo ｜ `[~]`→doing ｜ `[x]`→done ｜ `[!]`→block

## 产物自带交互能力（无需额外编码）

- 🌗 深/浅色主题切换（记忆偏好到 localStorage）
- 点击方块循环切换任务状态并自动保存
- 按状态 / 优先级筛选，空分组自动隐藏
- 顶部进度条 + 完成/进行中/阻塞/待办统计
- 里程碑时间轴视图
- ⬇ 导出回 Markdown（含当前勾选状态）
- 🖨 打印（自动隐藏工具栏）

## 示例

输入 `todolist.md` 片段：
```markdown
## 第 1 月 · M0
### M0 骨架跑通
- [x] `P0` 通读 **agentpool** 加载机制
- [~] `P0` 改造 main.py 进入对话循环
```

对应 `DATA` 片段：
```js
{
  title: "第 1 月 · M0", type: "tasks",
  subs: [{
    title: "M0 骨架跑通",
    tasks: [
      { p:"P0", status:"done",  t:"通读 <strong>agentpool</strong> 加载机制" },
      { p:"P0", status:"doing", t:"改造 main.py 进入对话循环" }
    ]
  }]
}
```

## 参考

- 更完整的解析约定与边界情况见 [reference.md](reference.md)
