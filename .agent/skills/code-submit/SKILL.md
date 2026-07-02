---
name: code-submit
description: >-
  轻量级代码提交 skill，专注于「审查变更 → stage → commit → 处理 pre-commit hook → push」的完整链路。
  当用户明确说「提交代码」「commit」「push」「提代码」「交代码」「合代码」时触发。
  与 git-master skill 互补：git-master 处理复杂 git 操作（rebase、历史搜索、精细拆分提交），
  而 code-submit 专注「快速审查变更并提交推送」这一线性流程。
  即使用户没有明确说 push，只要说了「提交代码」就应该帮他们完成 push。
---

# Code Submit Skill

## 核心原则

这是一个**轻量级、高成功率**的提交流程 skill。不处理 rebase、分支管理、历史重写等复杂操作（那些交给 git-master）。

### 流程概览

```
用户说「提交代码」
  → 审查变更（status + diff）
  → 检查文件大小（对大文件提示用户决定）
  → 智能 stage（排除不应该提交的文件）
  → 生成中文 commit 消息
  → 执行 commit
  → 如 pre-commit hook 失败，自动重试
  → push 到远程
  → 报告结果
```

---

## 执行步骤

### Step 1: 审查变更

并行执行以下命令，快速了解当前状态：

```bash
git status
git diff --stat          # 未暂存的变更概览
git diff --staged --stat # 已暂存的变更概览
git log --oneline -5     # 最近的 commit 风格参考
git branch --show-current
```

**关注点：**
- 有哪些文件被修改/新增/删除
- 有无 untracked 文件需要纳入
- 当前分支名和远程追踪情况
- 项目最近 commit 风格（虽然我们用中文，但了解一下项目习惯）

### Step 2: 审查文件内容（重要）

在 stage 之前，**至少 review 关键文件的 diff 内容**，确保：

1. 没有遗留的调试代码（console.log、print、TODO 等不应提交的内容）
2. 变更合理，没有明显的错误
3. 理解改动的业务含义，这样才能写出好的 commit 消息

```bash
git diff                 # 查看详细变更
```

### Step 3: 检查文件大小（重要）

在 stage 之前，先检查所有待提交文件的大小。**大文件会导致 pre-commit hook 失败（check-added-large-files），应提前处理。**

```bash
# 检查所有待提交文件的大小（含 untracked）
git status --porcelain | awk '{print $2}' | xargs ls -lh 2>/dev/null | sort -k5 -rh

# 或使用 du 精准查看每个文件
git status --porcelain | awk '{print $2}' | xargs du -sh 2>/dev/null | sort -rh
```

**检查标准（默认阈值：500KB）：**
- 文件 ≤ 500KB → 正常提交
- 文件 > 500KB → **必须询问用户**如何处理

**大文件处理选项（向用户呈现）：**

1. **不提交该文件** — 将文件移出 stage（`git rm --cached <file>`），后续用 `.gitignore` 忽略或用 Git LFS 管理
2. **强制提交** — 跳过 pre-commit 的文件大小检查（`--no-verify`），但需用户确认
3. **使用 Git LFS** — 如果项目已配置 LFS，指导用户通过 LFS 管理大文件

### Step 4: 规划 stage

决定哪些文件应该被纳入本次提交：

**应该 stage 的：**
- 有意义的代码变更
- 新增的文件（业务代码、配置文件等）

**不应该 stage 的（谨慎处理）：**
- 构建产物（dist/、build/、*.pyc 等）—— 通常在 .gitignore 里
- 临时文件、日志文件
- 超过 500KB 的大文件（除非用户确认要提交）
- `.omo/` 目录下的运行时数据（除非用户明确要求）
- 用户明确说不需要提交的文件

**如果文件较多，先与用户确认是否全部提交，特别是 untracked 文件。**

```bash
git add <file1> <file2> ...
```

### Step 5: 生成中文 commit 消息

用**中文**写 commit 消息。格式建议：

```
<type>: <简要描述改动>

<详细说明（可选）>
```

**常用的 type 前缀：**

| type | 适用场景 |
|------|----------|
| feat | 新功能 |
| fix | 修复 bug |
| refactor | 重构 |
| chore | 杂项（配置、依赖、文档等） |
| style | 代码格式调整 |
| docs | 文档变更 |
| test | 测试相关 |
| perf | 性能优化 |

**Commit 消息要求：**
- 第一行不超过 72 字符
- 简要说明改动的内容和原因
- 如果涉及多个不相关的改动，询问用户是否要拆分为多个 commit

### Step 6: 执行 Commit

```bash
git commit -m "<type>: <中文描述>"
```

### Step 7: 处理 Pre-commit Hook 失败

**这是最容易出问题的步骤，需要格外注意。**

如果 pre-commit hook 失败并自动修复了文件（比如修正了 trailing whitespace、EOF 结尾等）：

1. **不要慌** —— 这是正常情况，pre-commit hook 会自己修好小问题
2. 重新 stage 被修改的文件：
   ```bash
   git add -A
   ```
3. 重新 commit（复用相同的消息）：
   ```bash
   git commit -m "<相同的消息>"
   ```
4. 如果第二次还是失败，**仔细阅读错误信息**，判断是：
   - **可自动修复的问题**（trailing-whitespace、end-of-file-fixer 等）→ 重新 stage + commit
   - **check-added-large-files（文件过大）** → 询问用户：
     - 如果不想提交该大文件 → `git rm --cached <file>` 后重新 commit
     - 如果确实需要提交 → 使用 `--no-verify` 跳过检查（需用户确认）
   - **需要用户决策的其他问题** → 报告给用户，等待指示
   - **与当前改动无关的 pre-existing 问题** → 告知用户，可选择 `--no-verify` 跳过（但需要用户确认）

### Step 8: Push 到远程

```bash
git push
```

如果 push 失败（如远程有新的提交）：

```bash
git pull --rebase     # 先拉取远程变更
git push              # 再推送
```

如果当前分支没有 upstream：
```bash
git push -u origin <branch-name>
```

### Step 9: 报告结果

以简洁的方式告知用户最终结果：

```
✅ 已提交并推送

  Commit: abc1234 - feat: 添加用户登录功能
  分支: main → origin/main
  文件: 3 个文件变更，+45/-12 行
```

**不要长篇大论** —— 几行就行，用户只想知道「搞定了没」和「改了什么」。

---

## 参考示例

### 示例 1：常规提交

```
用户: 帮我提交代码

Step 1: git status → 看到 modified: src/user.py, src/utils.py
Step 2: git diff → review 变更内容
Step 3: git add src/user.py src/utils.py
Step 4: commit -m "feat: 添加用户注册校验功能"
Step 5: pre-commit 修正 trailing whitespace
Step 6: git add -A && git commit -m "feat: 添加用户注册校验功能"
Step 7: git push

结果: ✅ 已提交并推送
  Commit: a1b2c3d - feat: 添加用户注册校验功能
```

### 示例 2：Pre-commit 修复后自动重试

```
用户: 帮我提交代码

Step 1: git status
Step 2: review diff
Step 3: git add ...
Step 4: git commit → 失败！trailing-whitespace hook 修复了文件
Step 5: git add -A && git commit → 成功！
Step 6: git push → 成功！

结果: ✅ 已提交并推送
  Commit: e5f6g7h - fix: 修复导航栏点击无响应问题
```

### 示例 3：有 untracked 文件需要确认

```
用户: 帮我提交代码

git status 显示有 untracked 文件 .agent/skills/xxx/
→ 询问用户是否要纳入这些文件
→ 用户确认后 stage 所有文件
→ 后续流程相同
```

### 示例 4：大文件处理

```
用户: 帮我提交代码

Step 1: git status → 看到新增文件 result-card.png（858KB）
Step 2: review diff
Step 3: 检查文件大小 → 发现 result-card.png 858KB > 500KB
→ 询问用户："result-card.png (858KB) 超过 500KB 限制。是否要提交？"
→ 用户选择不提交
→ git rm --cached .agent/skills/darwin-skill/templates/result-card.png
Step 4: stage 其他文件
Step 5: commit → pre-commit 通过
Step 6: push

结果: ✅ 已提交并推送
  Commit: a1b2c3d - feat: 添加新 skill（result-card.png 已排除）
```

---

## 与 git-master 的协作

| 场景 | 使用哪个 skill |
|------|---------------|
| 「提交代码」「commit」「push」 | code-submit（当前 skill） |
| 「rebase」「squash」「整理 commit」 | git-master |
| 「找 bug 是哪个 commit 引入的」 | git-master |
| 「精细拆分多个 commit」 | git-master |
| 「需要 force push」 | 先尝试 code-submit，失败后转 git-master |

---

## 边界条件处理

### Dirty working directory（有未提交的改动）
- 如果 stage 之外还有未 stage 的改动，询问用户是否一起提交

### 大量文件变更（10+）
- 询问用户是否要分多次提交
- 如果用户说「一次性提交」，尊重用户决定

### 新分支首次 push
- 自动带上 `-u origin <branch-name>`

### Merge 冲突
- 如果是 `git pull --rebase` 导致冲突，报告给用户，不自行解决
- 这种情况超出本 skill 范围

### 提交时检测到敏感信息
- 如果发现密码、token、密钥等，警告用户并要求确认

### 大文件（>500KB）
- 在 stage 前使用 `git status --porcelain | awk '{print $2}' | xargs ls -lh` 检查文件大小
- 发现超过 500KB 文件时，询问用户是否提交
- 如果用户选择不提交，使用 `git rm --cached <file>` 从 stage 中移除
- 如果用户强制提交，使用 `--no-verify` 跳过 pre-commit 检查
- 对于项目中常见的大文件，建议配置 `.gitignore` 或过渡到 Git LFS
