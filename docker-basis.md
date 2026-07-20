# Docker 基础知识点

## 进入容器与退出

### 启动并进入容器

```bash
docker run -it <image> <shell>
# 示例
docker run -it ubuntu bash
```

### 退出容器

#### 交互式容器（`docker run -it` 启动的）

| 操作 | 效果 |
|---|---|
| `exit` 或 `Ctrl+D` | 退出并**停止**容器 |
| `Ctrl+P` + `Ctrl+Q` | 退出但**保持容器运行**（detach） |

#### 进入正在运行的容器（`docker exec -it`）

| 操作 | 效果 |
|---|---|
| `exit` 或 `Ctrl+D` | 退出并**不会**停止容器（exec 的进程结束而已） |

**总结：**
- 想要容器继续后台跑 → `Ctrl+P` `Ctrl+Q`
- 想让容器停止 → `exit` 或 `Ctrl+D`