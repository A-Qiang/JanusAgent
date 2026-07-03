# Docker 基础知识

> 面向 AI/ML 训练的 Docker 入门笔记，记录常用命令、核心概念和实战经验。

---

## 1. 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **Image（镜像）** | 只读模板，包含操作系统 + 依赖 + 代码的打包文件 | Python 类 |
| **Container（容器）** | 镜像的运行实例，可读写，可启动/停止/删除 | 类的实例 |
| **Repository（仓库）** | 镜像名，格式 `[registry/]name[:tag]` | GitHub 仓库 |
| **Registry（注册表）** | 存放镜像的中心仓库 | GitHub |
| **Tag（标签）** | 镜像的版本标识号 | Git tag |
| **Dockerfile** | 描述如何构建镜像的脚本 | setup.py |
| **Volume（卷）** | 容器外的持久化存储 | 外接硬盘 |

### 关系图

```
Dockerfile  (构建脚本)
     │ docker build
     ▼
   Image     (只读模板，如 nginx:latest)
     │ docker run
     ▼
 Container  (运行中的实例，可读写)
     │
     ├── docker stop    → 停止（不删除）
     ├── docker start   → 重新启动
     ├── docker rm      → 删除
     └── docker commit  → 保存为新镜像
```

---

## 2. 镜像管理

### 2.1 查看镜像

```bash
# 列出所有镜像
docker images

# 输出格式：
# REPOSITORY          TAG         IMAGE ID      CREATED       SIZE
# nginx               latest      abc12345      2 weeks ago   187MB
# rllm                verl-fixed  04ff985cc57c  7 days ago    33.4GB

# 查看镜像详情
docker inspect rllm:verl-official-v5

# 查看镜像的分层历史
docker history rllm:verl-official-v5

# 查看镜像的环境变量和启动命令
docker inspect rllm:verl-official-v5 | python3 -c "
import sys, json
data = json.load(sys.stdin)
for d in data:
    cfg = d.get('Config', {})
    print('Cmd:', cfg.get('Cmd'))
    print('Entrypoint:', cfg.get('Entrypoint'))
    print('WorkingDir:', cfg.get('WorkingDir'))
    for e in cfg.get('Env', []):
        print('Env:', e)
"

# 搜索镜像（Docker Hub）
docker search pytorch
```

### 2.2 拉取镜像

```bash
# 从 Docker Hub 拉
docker pull nginx:latest

# 从阿里云/私有仓库拉
docker pull registry.cn-hangzhou.aliyuncs.com/llm/vllm-openai:v0.18.0

# 从 verl 官方 Docker Hub
docker pull verlai/verl:vllm011.latest
docker pull verlai/verl:sgl055.latest
```

### 2.3 删除镜像

```bash
# 删除镜像（需要先删依赖它的容器）
docker rmi <image_id>
docker rmi rllm:verl-official-v5

# 清理无标签的 <none> 悬空镜像（dangling images）
docker image prune

# 清理所有不用的镜像（包括悬空和未被容器引用的）
docker image prune -a
```

---

## 3. 容器管理

### 3.1 创建并运行容器

```bash
# 基本用法
docker run [选项] 镜像名 [命令]

# 常用选项
--rm              # 容器退出后自动删除（适合临时任务）
-it               # 交互式终端（进去操作终端）
-d                # 后台运行（daemon）
--gpus all        # 暴露所有 GPU 给容器
--name mycontainer # 给容器命名
-v /host:/container  # 挂载卷（数据持久化）
-p 8080:80        # 端口映射（宿主机:容器）
--shm-size 10g    # 共享内存大小（PyTorch 训练必须，默认 64MB 不够）
--net=host        # 使用宿主机网络（减少网络开销）
--entrypoint      # 覆盖镜像默认入口程序
-w /workspace     # 设置工作目录
--cap-add=SYS_ADMIN  # 添加系统权限
```

### 3.1.1 docker create：创建但不运行

`docker run` = `docker create` + `docker start` 的合并。拆开用的场景：

- 创建容器后先做一些准备工作（拷文件、调参数），再启动
- 需要容器名/ID 提前固定，方便脚本引用
- GPU 训练中典型的「先创建、改配置、再启动」工作流

```bash
# 创建容器（不启动）
docker create --runtime=nvidia --gpus all --net=host \
    --shm-size="10g" -v .:/workspace/verl \
    --name verl verlai/verl:vllm011.latest sleep infinity

# 启动
docker start verl

# 进入
docker exec -it verl bash

# 在容器内开始训练
cd /workspace/verl && python train.py
```

**常用场景对比：**

| 场景 | `docker run` | `docker create + start` |
|------|-------------|------------------------|
| 临时跑一条命令，用完即删 | ✅ `--rm` 合适 | ❌ 多此一举 |
| 需要先拷文件再启动 | ❌ 不方便 | ✅ `docker cp` 后再 `start` |
| 调试镜像/检查 env | ⚠️ 也还行 | ✅ 先创建、`exec` 检查、再正式启动 |
| CI/CD 中分步编排 | ❌ 合并了不方便控制 | ✅ 清晰的 create → cp → start 步骤 |

```bash
# 常用 docker create 参数（与 docker run 一致）
--runtime=nvidia    # 使用 NVIDIA 容器运行时（GPU 必需）
--gpus all          # 暴露所有 GPU
--net=host          # 使用宿主机网络
--shm-size=10g      # 共享内存大小（PyTorch 训练必需）
-v /host:/container # 挂载卷
--name <name>       # 容器命名
--cap-add=SYS_ADMIN # 添加系统权限
```

> **注意：** `docker create` 的参数用法和 `docker run` 完全一致，唯一的区别是它只创建不启动。

### 3.2 实际例子

```bash
# 例1: 运行一次 nvidia-smi 就退出
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 例2: 交互式进入容器调试
docker run -it --rm --gpus all --shm-size=10g rllm:verl-official-v5 bash

# 例3: 覆盖 entrypoint（镜像的启动命令不对时）
docker run -it --rm --entrypoint python3 rllm:verl-official-v5 -c "import verl; print('ok')"

# 例4: 挂载代码目录 + 后台长期运行
docker run -d --gpus all --shm-size=10g \
    -v /home/user/project:/workspace \
    --name my_job \
    rllm:verl-official-v5 \
    python3 train.py
```

### 3.3 容器生命周期

```bash
docker ps                     # 查看运行中的容器
docker ps -a                  # 查看所有容器（含已停止）
docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"  # 自定义格式

docker start <container_id>   # 启动已停止的容器
docker stop <container_id>    # 停止容器
docker restart <container_id> # 重启容器

docker rm <container_id>      # 删除容器
docker container prune        # 清理所有已停止的容器

docker logs <container_id>    # 查看容器日志
docker logs -f <container_id> # 持续跟踪日志（tail -f）
```

---

## 4. 数据持久化

容器删除后内部数据会丢失。需要用 Volume 或 Bind Mount 来持久化。

```bash
# 方式1: Bind Mount（推荐，挂载宿主机目录）
docker run -v /real/path:/container/path ...

# 方式2: Volume（Docker 管理）
docker volume create mydata
docker run -v mydata:/container/path ...

# 方式3: 仅挂载子目录（只读）
docker run -v /host/path:/container/path:ro ...

# 实际例子：训练代码在宿主机，数据也持久化
docker run --gpus all --shm-size=10g \
    -v /home/user/verl:/workspace/verl \
    -v /home/user/data:/workspace/data \
    -v /home/user/checkpoints:/workspace/checkpoints \
    -it rllm:verl-official-v5 bash
```

---

## 5. 查看资源占用

```bash
# 查看 Docker 整体磁盘占用
docker system df

# 输出示例：
# TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
# Images          45        12        168.2GB   89.3GB (53%)
# Containers      8         3         2.5GB     1.2GB (48%)
# Local Volumes   5         2         1.8GB     0B (0%)
# Build Cache     0         0         0B        0B

# 查看运行中容器的资源使用（CPU/内存/GPU）
docker stats

# 查看特定容器资源
docker stats <container_name>

# 查看容器内进程
docker top <container_id>
```

---

## 6. Dockerfile 快速入门

```dockerfile
# 基础镜像
FROM nvidia/cuda:12.8.1-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git wget curl build-essential python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 包
RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# 复制代码
COPY . /workspace
WORKDIR /workspace

# 安装项目
RUN pip3 install -e .

# 默认启动命令
CMD ["bash"]
```

### 常用指令

| 指令 | 说明 | 每次 build 都重新执行？ |
|------|------|----------------------|
| `FROM` | 基础镜像 | — |
| `RUN` | 执行命令 | 仅当上游或命令变更时 |
| `COPY` | 复制文件 | 仅当文件变更时 |
| `ENV` | 设置环境变量 | 否 |
| `WORKDIR` | 设置工作目录 | 否 |
| `CMD` | 默认启动命令 | 否 |
| `ENTRYPOINT` | 固定入口程序 | 否 |
| `ARG` | Build 时参数 | 否 |

---

## 7. 实战技巧

### 7.1 GPU 相关

```bash
# 确认容器内能看到 GPU
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 指定特定 GPU（只让容器看到 0,1 号卡）
docker run --gpus '"device=0,1"' ...

# 查看 NVIDIA 驱动版本（宿主机）
nvidia-smi
```

### 7.2 PyTorch 训练注意事项

```bash
# 共享内存必须给够（PyTorch DataLoader 多进程用）
docker run --shm-size=10g ...

# 或者挂载 /dev/shm
docker run -v /dev/shm:/dev/shm ...
```

### 7.3 网络相关

```bash
# 使用宿主机网络（性能更好，适合分布式训练）
docker run --net=host ...

# 端口映射（宿主机 8080 → 容器 80）
docker run -p 8080:80 ...
```

### 7.4 清理磁盘空间（重要！）

Docker 用久了会占大量磁盘。定期清理：

```bash
# 安全清理（不影响运行中的容器）
docker image prune          # 删悬空镜像
docker container prune      # 删已停止容器
docker volume prune         # 删未被使用的卷
docker builder prune        # 删 build 缓存

# 一键清理所有未使用资源
docker system prune -a --volumes
```

### 7.5 容器内和宿主机传文件

```bash
# 宿主机 → 容器
docker cp /host/file.txt container_name:/container/path/

# 容器 → 宿主机
docker cp container_name:/container/file.txt /host/path/
```

---

## 8. 常见问题

### Q: 镜像太多占磁盘怎么办？
A: `docker system df` 看谁占的多，`docker image prune` 清理无标签镜像。

### Q: 容器退出后数据会丢吗？
A: 会。容器内写入的数据只存在于该容器。用 `-v` 挂载卷来持久化。

### Q: `docker run --rm` 和不用 `--rm` 的区别？
A: `--rm` 退出自动删容器，不留垃圾。不加的话容器会保留（`docker ps -a` 可见），可以 `docker start` 重启。

### Q: 容器里没有 `nvidia-smi`？
A: 确保加了 `--gpus all`，并且宿主机有 NVIDIA 驱动 + nvidia-container-toolkit。

### Q: 怎么进一个已经在跑的容器？
```bash
docker exec -it <container_name> bash
```

### Q: 如何退出容器的 bash 会话？
A: 在容器 bash 里输入 `exit` 或按 `Ctrl + D`，只退出 bash（`docker exec` 结束），容器本身继续运行。要停止容器需在宿主机执行 `docker stop <name>`。

### Q: `ENTRYPOINT` 和 `CMD` 什么区别？
A: `ENTRYPOINT` 是固定入口（如 `python3`），`CMD` 是默认参数（如 `app.py`）。运行 `docker run image train.py` 时，实际执行的是 `entrypoint + 你给的参数`，而不是 `entrypoint + cmd`。

---

## 9. 本服务器镜像一览（2026-07-02 记录）

| 镜像 | 大小 | 用途 |
|------|------|------|
| `rllm:verl-official-v5` | 33.4GB | verl 0.7.1 + torch 2.8.0 + vllm 0.11.0 + ray 2.49.2 |
| `lmsysorg/sglang:latest` | 29.2GB | SGLang 官方镜像（支持多轮 RL） |
| `vllm/vllm-openai:v0.18.0` | 22.4GB | vLLM 推理引擎 |
| `python-dev-cn:3.12` | 641MB | Python 3.12 开发环境 |
| `irootechimages-registry-vpc/.../vllm-openai:glm52-dcp` | 18.7GB | 定制版 vLLM |

---

> 最后更新: 2026-07-02