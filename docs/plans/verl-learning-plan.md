# verl 学习计划

> **目标**: 学习 [verl](https://github.com/verl-project/verl)（HybridFlow）—— 字节跳动开源的 LLM 强化学习后训练框架，为 JanusAgent 的 `agent-rl` 包引入 RL 训练能力。
>
> **verl 核心**: verl = Volcano Engine Reinforcement Learning for LLMs，是 [HybridFlow: A Flexible and Efficient RLHF Framework](https://arxiv.org/abs/2409.19256v2) (EuroSys 2025) 的开源实现。

---

## 学习路径概览

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| **Phase 1** | 背景知识补齐 | 1-2 天 |
| **Phase 2** | 环境搭建 | 0.5-1 天 |
| **Phase 3** | 快速上手 — PPO 训练 | 1 天 |
| **Phase 4** | 深入架构 — HybridFlow 编程模型 | 2-3 天 |
| **Phase 5** | 多种 RL 算法实践 | 2-3 天 |
| **Phase 6** | 进阶主题 | 2-3 天 |
| **Phase 7** | 结合 agent-rl 项目实战 | 3-5 天 |

---

## Phase 1: 背景知识补齐

### 1.1 强化学习基础

- [ ] **RL 核心概念**
  - Policy (策略) / Value Function (价值函数) / Reward (奖励) / State-Action 空间
  - On-policy vs Off-policy 的区别
  - Importance Sampling（重要性采样）
- [ ] **PPO (Proximal Policy Optimization)**
  - Clip 机制与 Trust Region
  - Actor-Critic 架构
  - Advantages Estimation (GAE)
- [ ] **GRPO (Group Relative Policy Optimization)**
  - DeepSeek-R1 中使用的算法
  - 无 Critic 模型，基于 Group 内奖励比较
  - 与 PPO 的关键区别
- [ ] **RLHF 整体流程**
  - SFT → Reward Model → RL 的三阶段范式
  - 规则奖励 vs 模型奖励

### 1.2 LLM 分布式训练基础

- [ ] **FSDP / FSDP2** — PyTorch 全分片数据并行
  - 理解 ZeRO Stage 3 原理
  - 分片策略: full_shard, hybrid_shard
- [ ] **Megatron-LM** — 张量并行 + 流水线并行
  - 适用于 10B+ 级别的大模型
- [ ] **vLLM / SGLang** — LLM 推理加速引擎
  - PagedAttention / RadixAttention
  - 在 RL 中作为 rollout 生成引擎
- [ ] **Ray** — 分布式计算框架
  - Ray Actors, Remote Functions, Ray Cluster

### 1.3 推荐资料

| 主题 | 资源 |
|------|------|
| PPO 论文 | [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347) |
| GRPO 论文 | [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948) |
| HybridFlow | [HybridFlow: A Flexible and Efficient RLHF Framework](https://arxiv.org/abs/2409.19256v2) |
| DAPO | [DAPO: An Open-Source RL System from Scratch](https://dapo-sia.github.io/) |
| FSDP 教程 | [PyTorch FSDP 官方文档](https://pytorch.org/docs/stable/fsdp.html) |
| vLLM 文档 | [vLLM 官方文档](https://docs.vllm.ai/) |

---

## Phase 2: 环境搭建

### 2.1 硬件要求

- GPU: **NVIDIA GPU, ≥24GB HBM**（单卡可跑 0.5B-1.5B 模型）
- CUDA: ≥12.8
- 推荐: 4× 及以上 GPU（多卡体验完整分布式训练）

### 2.2 安装方式

**推荐方式 A — Docker 镜像（最稳定）**:

```bash
# 拉取预构建镜像
docker pull verlai/verl:vllm011.latest   # vLLM 后端
# 或
docker pull verlai/verl:sgl055.latest    # SGLang 后端

# 启动
docker create --runtime=nvidia --gpus all --net=host --shm-size="10g" \
  --cap-add=SYS_ADMIN -v .:/workspace/verl --entrypoint sleep --name verl verlai/verl:vllm011.latest infinity
docker start verl
docker exec -it verl bash

**参数解释：**

| 参数 | 说明 |
|------|------|
| `--runtime=nvidia` | 使用 NVIDIA 容器运行时，**GPU 访问必需** |
| `--gpus all` | 暴露所有 GPU 给容器，也可用 `--gpus '"device=0,1"'` 限制特定卡 |
| `--net=host` | 使用宿主机网络栈，避免 NAT 开销，多节点 NCCL 通信必需 |
| `--shm-size="10g"` | 共享内存设为 10GB，PyTorch DataLoader 多进程传数据必需（默认 64MB 不够） |
| `--cap-add=SYS_ADMIN` | 授予内核能力，用于 profiler/内核参数调整（非必需，大部分训练不需要） |
| `-v .:/workspace/verl` | 挂载当前目录到容器内 `/workspace/verl`，代码在宿主机编辑、容器内运行 |
| `--name verl` | 容器命名为 `verl`，方便后续 `docker exec -it verl bash` 进入 |
| `verlai/verl:vllm011.latest` | 镜像名:tag，对应 vLLM 0.11.x 后端的 verl 官方镜像 |
| `sleep infinity` | 容器启动后永久睡眠，保持容器运行等待用户进入 |

> `docker create` 只创建不启动，参数用法与 `docker run` 完全一致。之后手动 `docker start` 启动、`docker exec` 进入（详见 `docs/docker/docker-basics.md` §3.1.1）。

# 安装 verl
git clone https://github.com/verl-project/verl && cd verl
pip3 install --no-deps -e .
```

**方式 B — 从源码安装（可开发调试）**:

```bash
# 创建 conda 环境
conda create -n verl python==3.12
conda activate verl

# 使用安装脚本（会自动处理 vllm/sglang/megatron 等依赖）
git clone https://github.com/verl-project/verl.git
cd verl
bash scripts/install_vllm_sglang_mcore.sh

# 仅 FSDP 后端（轻量）
USE_MEGATRON=0 bash scripts/install_vllm_sglang_mcore.sh

# 安装 verl 本体
pip install --no-deps -e .
```

### 2.3 验证安装

```bash
# 检查关键依赖
python -c "import verl; print('verl OK')"
python -c "import ray; print(ray.__version__)"
python -c "import vllm; print(vllm.__version__)"

```

---

## Phase 3: 快速上手 — PPO 训练

### 3.1 目标

在 **GSM8K 数学数据集** 上完整跑通 PPO 训练流程，理解 verl 命令行配置体系。

### 3.2 步骤

- [ ] **Step 1**: 数据预处理
  ```bash
  python3 examples/data_preprocess/gsm8k.py --local_save_dir ~/data/gsm8k
  ```
- [ ] **Step 2**: 下载基础模型
  ```bash
  python3 -c "import transformers; transformers.pipeline('text-generation', model='Qwen/Qwen2.5-0.5B-Instruct')"
  ```
- [ ] **Step 3**: 启动 PPO 训练
  ```bash
  PYTHONUNBUFFERED=1 python3 -m verl.trainer.main_ppo \
    data.train_files=$HOME/data/gsm8k/train.parquet \
    data.val_files=$HOME/data/gsm8k/test.parquet \
    data.train_batch_size=256 \
    data.max_prompt_length=512 \
    data.max_response_length=512 \
    actor_rollout_ref.model.path=Qwen/Qwen2.5-0.5B-Instruct \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.actor.ppo_mini_batch_size=64 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=8 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.4 \
    actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=4 \
    critic.optim.lr=1e-5 \
    critic.model.path=Qwen/Qwen2.5-0.5B-Instruct \
    critic.ppo_micro_batch_size_per_gpu=4 \
    algorithm.kl_ctrl.kl_coef=0.001 \
    trainer.logger='["console","wandb"]' \
    trainer.val_before_train=False \
    trainer.n_gpus_per_node=1 \
    trainer.nnodes=1 \
    trainer.save_freq=10 \
    trainer.test_freq=10 \
    trainer.total_epochs=15 2>&1 | tee verl_demo.log
  ```

### 3.3 关键观察指标

| 指标 | 含义 |
|------|------|
| `val/test_score/` | 验证集奖励分数（核心指标） |
| `actor/pg_loss` | 策略梯度损失 |
| `critic/vf_loss` | 价值函数损失 |
| `actor/entropy_loss` | 策略熵（探索程度） |
| `actor/reward_kl_penalty` | KL 惩罚项 |
| `response_length/mean` | 模型回复长度 |
| `critic/rewards/mean` | 奖励均值 |

### 3.4 模型保存与合并

```bash
# 合并 FSDP 分片权重为 HuggingFace 格式
python3 -m verl.model_merger merge \
    --backend fsdp \
    --local_dir checkpoints/${project}/${experiment}/global_step_${N}/actor \
    --target_dir checkpoints/${project}/${experiment}/global_step_${N}/actor/huggingface
```

---

## Phase 4: 深入架构 — HybridFlow 编程模型

### 4.1 理解 verl 核心设计哲学

verl 将 RL 训练抽象为**两级数据流**:

```
┌──────────────────────────────────────────────┐
│           Control Flow (单进程)               │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐   │
│  │ Rollout │→ │Advantage │→ │Actor/Critic│   │
│  │ (采样)  │  │(优势计算) │  │  (策略更新) │   │
│  └────┬────┘  └──────────┘  └──────┬─────┘   │
│       │                            │          │
└───────┼────────────────────────────┼──────────┘
        │  DataProto (跨进程数据)     │
  ┌─────▼────────────────────────────▼──────┐
  │          Computation Flow (多进程)       │
  │  ┌─────────┐  ┌──────────┐  ┌────────┐  │
  │  │  vLLM   │  │   FSDP   │  │Critic  │  │
  │  │(rollout)│  │ (actor)  │  │ (value)│  │
  │  └─────────┘  └──────────┘  └────────┘  │
  └──────────────────────────────────────────┘
```

**关键设计亮点**:

1. **解耦 Control Flow 与 Computation Flow**
   - Controller 是单进程 Python 程序
   - 通过 Ray 与 WorkerGroup 交互
   - 新增 RL 算法只需修改 Control Flow
   - Computation Flow 可在 FSDP / Megatron 间无缝切换

2. **`@register(dispatch_mode=...)` 装饰器**
   - 自动处理数据分片/分发/收集
   - 让分布式运算调用起来像单进程

### 4.2 代码库结构阅读

```python
verl/
├── trainer/
│   ├── main_ppo.py          # 入口: RL 训练
│   ├── main_grpo.py         # 入口: GRPO 训练
│   ├── main_sft.py          # 入口: SFT 训练
│   └── ppo/ray_trainer.py   # PPO 训练主循环
│
├── workers/
│   ├── engine_workers.py    # ActorRolloutRefWorker / TrainingWorker
│   ├── protocol.py          # DataProto 数据接口
│   └── engine/
│       ├── fsdp/            # FSDP 训练引擎
│       └── megatron/        # Megatron-LM 训练引擎
│
├── config/
│   └── ppo_trainer.yaml     # 配置模板
│
├── utils/
│   ├── dataset/             # 数据集处理
│   ├── reward_score/
│   │   ├── gsm8k.py         # GSM8K 规则奖励
│   │   └── math.py          # MATH 规则奖励
│   └── seqlen_balancing.py  # 序列长度平衡
│
└── third_party/
    └── vllm/                # vLLM 适配层
```

### 4.3 PPO 训练循环源码精读

```python
# verl/trainer/ppo/ray_trainer.py (概念简化)
for batch in dataloader:
    # 1. Rollout: 用 Actor 生成回复
    responses = actor_rollout_ref_wg.generate_sequences(prompts)

    # 2. 计算旧策略 log_prob
    old_log_probs = actor_rollout_ref_wg.compute_log_prob(responses)

    # 3. 计算参考策略 log_prob
    ref_log_probs = actor_rollout_ref_wg.compute_ref_log_prob(responses)

    # 4. 计算 Value
    values = critic_wg.compute_values(responses)

    # 5. 计算 Reward
    rewards = reward_wg.compute_scores(responses)

    # 6. 计算 Advantage (GAE)
    advantages = compute_gae(values, rewards)

    # 7. 更新 Actor (PPO clip)
    actor_rollout_ref_wg.update_actor(data_with_advantages)

    # 8. 更新 Critic
    critic_wg.update_critic(data_with_advantages)
```

### 4.4 阅读 HybridFlow 论文

- [arXiv: HybridFlow: A Flexible and Efficient RLHF Framework](https://arxiv.org/abs/2409.19256v2)
- 重点章节: §3 系统设计, §4 Hybrid Controller, §5 3D-HybridEngine

---

## Phase 5: 多种 RL 算法实践

### 5.1 GRPO (DeepSeek-R1 风格)

GRPO 不需要 Critic 模型，通过 Group 内奖励对比来更新策略。

```bash
# GRPO 训练示例
python3 -m verl.trainer.main_ppo \
    algorithm.adv_estimator=grpo \
    data.train_files=... \
    actor_rollout_ref.model.path=Qwen/Qwen2.5-1.5B-Instruct \
    actor_rollout_ref.actor.ppo_mini_batch_size=256 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=8 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.5 \
    trainer.n_gpus_per_node=4 \
    ...
```

### 5.2 DAPO (Dynamic Sampling Policy Optimization)

DAPO 是开源的 SOTA RL 算法，在 AIME 2024 上基于 Qwen2.5-32B 达到 50 分。

```bash
# DAPO Recipe 位于 recipe/dapo/

# Clip 方式: 采样高奖励样本
algorithm.adv_estimator=dapo
algorithm.kl_ctrl.kl_coef=0.0  # DAPO 不使用 KL
```

### 5.3 更多算法

| 算法 | 目录 | 特点 |
|------|------|------|
| PPO | `examples/ppo_trainer/` | 经典 Actor-Critic |
| GRPO | `examples/grpo_trainer/` | 无 Critic，Group 奖励 |
| RLOO | `examples/rloo_trainer/` | REINFORCE Leave-One-Out |
| ReMax | `examples/remax_trainer/` | REINFORCE with Max baseline |
| REINFORCE++ | verl 内置 | REINFORCE 增强版 |
| DAPO | `verl-recipe/dapo/` | Dynamic Sampling |
| PRIME | `verl-recipe/prime/` | Process Reward Model |
| GSPO | `verl-recipe/gspo/` | Self-Play Optimization |
| DrGRPO | `verl-recipe/drgrpo/` | Dynamic Regularized GRPO |
| VAPO | [论文](https://arxiv.org/pdf/2504.05118) | Value-based Augmented PPO |
| PF-PPO | [论文](https://arxiv.org/abs/2409.06957) | Preference-Filtered PPO |

---

## Phase 6: 进阶主题

### 6.1 多轮交互与工具调用

- [ ] **Agent Loop**: 支持多轮交互的 RL 训练（tool calling）
- [ ] **Reward Loop**: 可编程的奖励计算流程
- [ ] 参考: `examples/tutorial/agent_loop_get_started/`

### 6.2 VLM 多模态 RL

- [ ] 使用 Qwen2.5-VL + verl 进行多模态 RL
- [ ] 参考: `examples/grpo_trainer/run_qwen2_5_vl_7b_fsdp.sh`

### 6.3 性能调优

- [ ] 阅读 [Performance Tuning Guide](https://verl.readthedocs.io/en/latest/perf/perf_tuning.html)
- [ ] 3D-HybridEngine: actor 模型的 Resharding
- [ ] vLLM GPU 内存利用率调优 (`gpu_memory_utilization`)
- [ ] 微批次大小 (`ppo_micro_batch_size_per_gpu`) 调优

### 6.4 LoRA + RL

- [ ] 使用 LoRA 降低 RL 训练的显存需求
- [ ] 参考: `examples/tuning/lora/run_qwen3_8b_fsdp.sh`
- [ ] 文档: [LoRA RL](https://verl.readthedocs.io/en/latest/advance/ppo_lora.html)

### 6.5 扩展阅读

| 主题 | 链接 |
|------|------|
| verl 正式文档 | [verl.readthedocs.io](https://verl.readthedocs.io/en/latest/) |
| verl-recipe (算法复现) | [github.com/verl-project/verl-recipe](https://github.com/verl-project/verl-recipe) |
| Awesome ML-SYS Tutorial | [verl 中文教程合集](https://github.com/zhaochenyang20/Awesome-ML-SYS-Tutorial) |
| 最佳实践 — 火山引擎 | [GRPO 分布式训练最佳实践](https://www.volcengine.com/docs/6459/1463942) |
| 技术 Talk 中文 | [verl HybridFlow 解读](https://hcqnc.xetlk.com/sl/3vACOK) |
| 知乎: PPO 数据流 | [PPO 数据流图详解](https://zhuanlan.zhihu.com/p/635757674) |
| AMD ROCm 支持 | [AMD verl 部署指南](https://rocm.blogs.amd.com/artificial-intelligence/verl-large-scale/README.html) |

---

## Phase 7: 结合 agent-rl 项目实战

### 7.1 项目现状

```
packages/agent-rl/
├── pyproject.toml          # uv workspace 子包，依赖空
├── README.md               # RL Face 定位说明
└── src/agent_rl/
    └── __init__.py         # 空包
```

### 7.2 整合方向

| 方向 | 具体内容 | 优先级 |
|------|---------|--------|
| **依赖引入** | 将 verl 及其依赖（vLLM, ray, FSDP）作为 agent-rl 的可选依赖 | P0 |
| **训练脚本化** | 封装 verl 命令行训练为 Python API，与 JanusAgent 的 YAML 配置体系对齐 | P1 |
| **Reward 函数定制** | 实现自定义规则奖励（如 GSM8K 数学格式奖励），参考 `verl/utils/reward_score/` | P1 |
| **数据集接入** | 实现数据预处理 pipeline，支持 HuggingFace datasets 格式 | P1 |
| **Agent Loop 集成** | 将 JanusAgent 的 Agent 能力与 verl 的多轮 RL 训练结合 | P2 |
| **实验跟踪** | 集成 wandb / mlflow 实验跟踪 | P2 |
| **Model Zoo 接入** | 支持 HuggingFace 主流模型（Qwen, LLaMA, DeepSeek）的一键训练 | P2 |

### 7.3 整合步骤

**Step 1**: 添加 verl 依赖到 `pyproject.toml`

```toml
[project]
dependencies = []

[project.optional-dependencies]
verl = [
    "verl",
    "vllm",
    "ray[data,train,tune,serve]",
    "torch>=2.5",
]
```

**Step 2**: 封装训练入口

```python
# src/agent_rl/trainer.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RLTrainingConfig:
    algorithm: str = "grpo"           # ppo, grpo, dapo, etc.
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"
    train_files: str = ""
    val_files: str = ""
    train_batch_size: int = 256
    max_prompt_length: int = 512
    max_response_length: int = 512
    n_gpus_per_node: int = 1
    nnodes: int = 1
    output_dir: str = "./checkpoints"
    # ... more config

class VerlTrainer:
    def __init__(self, config: RLTrainingConfig):
        self.config = config
        # Build command-line args from config

    def train(self):
        """Launch verl training with subprocess (flexible),
        or eventually import verl modules directly."""
        ...
```

**Step 3**: 编写自定义奖励函数

```python
# src/agent_rl/rewards/gsm8k_reward.py
# 参考 verl/utils/reward_score/gsm8k.py 的规则奖励实现
```

### 7.4 学习路线图

```
Week 1-2:  Phase 1-3 → 跑通环境 + 第一个 PPO 训练
Week 3-4:  Phase 4   → 深入理解 HybridFlow 源码
Week 5-6:  Phase 5   → GRPO / DAPO 算法实践
Week 7-8:  Phase 6   → Agent Loop / VLM / 性能调优
Week 9-12: Phase 7   → 整合到 agent-rl 包
```

---

## 附录

### A. 常见问题

**Q: 单卡 GPU 内存不足怎么办？**
A: 使用小模型（0.5B）+ 降低 `ppo_micro_batch_size_per_gpu` 和 `gpu_memory_utilization`
或使用 LoRA RL 方式

**Q: 训练过程中遇到 NaN loss 怎么办？**
A: 检查学习率是否过高（建议 lr ≤ 1e-5）；检查 KL 系数是否合适

**Q: vLLM 和 SGLang 如何选择？**
A: vLLM 生态更完善适合生产；SGLang 在多轮 RL 和 VLM RL 上有独特优化

### B. 性能监控

```bash
# 开启 wandb
trainer.logger='["console","wandb"]'
trainer.project_name=my_project
trainer.experiment_name=ppo_gsm8k

# 开启 TensorBoard
trainer.logger='["console","tb"]'
```

### C. 参考链接

- [verl GitHub](https://github.com/verl-project/verl)
- [verl 文档](https://verl.readthedocs.io/en/latest/)
- [HybridFlow 论文](https://arxiv.org/abs/2409.19256v2)
- [verl-recipe](https://github.com/verl-project/verl-recipe)
- [DAPO 主页](https://dapo-sia.github.io/)
- [PyTorch FSDP](https://pytorch.org/docs/stable/fsdp.html)