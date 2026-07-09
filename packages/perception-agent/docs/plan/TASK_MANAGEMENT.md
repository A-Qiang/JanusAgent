# 任务管理看板 — MinerU2.5 微调项目

> 框架：**OKR（月度）→ 需求（周级）→ 任务（天级）**
> 总周期：~4 周（2026-07-09 → 2026-08-05）

---

# 🎯 OKR-01：7月下半月 — 打好基础，跑通首条训练链路

**Objective**: 建立 MinerU2.5 微调的全套工程管线，跑通第一条 LoRA 训练-评估闭环。

| Key Result | 衡量标准 | 当前状态 |
|---|---|---|
| KR-1.1 | 能在本地用 ms-swift 正常加载 MinerU2.5 并执行一次推理 | 🔴 未开始 |
| KR-1.2 | 跑通第一条 LoRA SFT 管线（含数据加载、训练、checkpoint 保存） | 🔴 未开始 |
| KR-1.3 | 完成第一次模型评估，产出质量报告 | 🔴 未开始 |

---

## 📋 需求-01-1：环境与模型验证

**里程碑**：ms-swift + MinerU 本地运行畅通

### 每日任务

| 日期 | 任务 | 交付物 | 优先级 | 状态 |
|------|------|--------|--------|------|
| D1 | **研读 MinerU2.5 论文**<br>读 [2509.22186](https://arxiv.org/abs/2509.22186)、[2604.04771](https://arxiv.org/abs/2604.04771)<br>重点：数据引擎、两阶段策略、特殊 token 体系 | 论文笔记 | 🔥 HIGH | 🔴 待办 |
| D2 | **MinerU 推理实操**<br>`test_mineru_model.py --info` 看配置<br>`test_mineru_model.py --dry-run` 加载模型<br>`test_mineru_model.py --tiny` 跑推理 | 成功截图/输出记录 | 🔥 HIGH | 🔴 待办 |
| D3 | **ms-swift 框架入门**<br>`pip install ms-swift -U`<br>跑通 OCR 示例：`bash examples/train/multimodal/ocr.sh`<br>验证 MinerU 注册：`MODEL_MAPPING` 含 `qwen2_vl`<br>体验 Web-UI：`swift web-ui` | 终端日志 | 🔥 HIGH | 🔴 待办 |

### 验收条件
- [ ] `swift infer --model /home/zengqiang/models/MinerU2.5-Pro-2605-1.2B` 成功输出
- [ ] `ocr.sh` 训练跑完至少一个 epoch
- [ ] Web-UI 正常打开

---

## 📋 需求-01-2：项目脚手架搭建

**里程碑**：标准化工程目录 + 首次数据 Pipeline

### 每日任务

| 日期 | 任务 | 交付物 | 优先级 | 状态 |
|------|------|--------|--------|------|
| D4 | **工程目录与依赖锁定**<br>创建 `finetune/` 子目录（configs/data/scripts/experiments）<br>pyproject.toml 添加 ms-swift 依赖<br>验证 CUDA / PyTorch / Flash Attention 版本 | 目录结构+依赖锁 | ⚡ MEDIUM | 🔴 待办 |
| D5 | **首次数据 Pipeline**<br>收集第一份公开文档数据集（如 LaTeX_OCR）<br>验证 JSONL 格式是否兼容 ms-swift<br>写一个 `prepare_data.py` 做数据前处理 | data 目录 + 脚本 | ⚡ MEDIUM | 🔴 待办 |

### 验收条件
- [ ] `cd finetune/ && pip install -e .` 无报错
- [ ] `python prepare_data.py` 产出一条格式正确的 JSONL
- [ ] `swift sft --dataset` 能识别该 JSONL

---

# 🎯 OKR-02：8月上半月 — 训练迭代，产出可用的解析模型

**Objective**: 通过多轮实验找到最优微调配置，产出可在实际文档上工作的解析模型。

| Key Result | 衡量标准 | 当前状态 |
|---|---|---|
| KR-2.1 | 完成 ≥3 组对比实验（不同 lora_rank、freeze 策略、lr） | 🔴 未开始 |
| KR-2.2 | 最佳模型的 Text ED ≤ 0.10（OmniDocBench 子集） | 🔴 未开始 |
| KR-2.3 | 模型能通过 vLLM 部署并通过 REST API 调用 | 🔴 未开始 |

---

## 📋 需求-02-1：首次 LoRA 微调

**里程碑**：完整跑完一条 LoRA SFT 管线（数据→训练→保存→推理）

### 每日任务

| 日期 | 任务 | 交付物 | 优先级 | 状态 |
|------|------|--------|--------|------|
| D6 | **数据集整理**<br>清洗原始数据，保证输出-标注对齐<br>拆分 train/val/test（8:1:1）<br>写数据预览报告（样本数、图像分辨率分布） | 清洗后 JSONL + 报告 | 🔥 HIGH | 🔴 待办 |
| D7 | **LoRA SFT 第一次运行**<br>复制 `ocr.sh` 修改为 MinerU 配置<br>lr=1e-4, lora_rank=8, freeze_vit=true<br>per_device_batch=1, grad_accum=16<br>盯住 loss 曲线，记录显存占用 | 训练日志 + CSV loss | 🔥 HIGH | 🔴 待办 |
| D8 | **结果初步评估**<br>Merge LoRA 权重：`swift export --merge_lora true`<br>用 `swift infer` 在验证集上做定性评测<br>记录 bad cases（排版混乱/OOM/乱码） | 评估报告 | 🔥 HIGH | 🔴 待办 |

### 验收条件
- [ ] 训练完成一个 experiment 且 loss 收敛
- [ ] merge-lora 后推理有合理输出
- [ ] bad case 列表入库

---

## 📋 需求-02-2：超参数调优实验

**里程碑**: 确定最佳超参数组合

### 每日任务

| 日期 | 任务 | 交付物 | 优先级 | 状态 |
|------|------|--------|--------|------|
| D9 | **学习率搜索实验**<br>固定 lora_rank=8，跑 lr ∈ {5e-5, 1e-4, 2e-4}<br>记录每个 lr 的收敛速度和最终 loss | 对照表 | ⚡ MEDIUM | 🔴 待办 |
| D10 | **LoRA Rank 对比实验**<br>固定 lr=1e-4，跑 rank ∈ {8, 16, 32, 64}<br>记录推理质量差异和推理速度 | 对照表 | ⚡ MEDIUM | 🔴 待办 |
| D11 | **冻结策略对比实验**<br>策略1: freeze_vit=true（现状）<br>策略2: freeze_vit=false, lora 全量<br>策略3: `tuner_type=lora_llm`（ViT 全参+LLM lora） | 对照表 | ⚡ MEDIUM | 🔴 待办 |
| D12 | **消融实验总结**<br>汇总 9 组实验结果为矩阵表<br>选最优配置，写入 `configs/best.yaml` | 实验总结 + YAML | 🔥 HIGH | 🔴 待办 |

### 验收条件
- [ ] 实验矩阵表填满 9+ 行
- [ ] `best.yaml` 文件提交

---

## 📋 需求-02-3：进阶训练探索

**里程碑**: 在 LoRA 之外尝试更多训练技术

### 每日任务

| 日期 | 任务 | 交付物 | 优先级 | 状态 |
|------|------|--------|--------|------|
| D13 | **Packing + 多卡训练**<br>启用 `--packing true` 训练加速<br>尝试 NPROC_PER_NODE=2 DeepSpeed ZeRO2<br>对比 packing 前后的吞吐（samples/s） | 提速对比表 | ⚡ MEDIUM | 🔴 待办 |
| D14 | **GRPO 强化学习训练**<br>配置 `swift rlhf --rlhf_type grpo`<br>实现文档解析奖励函数（format + 版面准确度）<br>小批量试跑 50 step 验证流程通顺 | GRPO 训练日志 | 🔵 LOW | 🔴 待办 |

### 验收条件
- [ ] Packing 实验显示 ≥1.5× 吞吐提升
- [ ] GRPO 管线无报错走完至少一轮

---

## 📋 需求-02-4：评估 + 部署

**里程碑**: 量化评估达标，模型可对外服务

### 每日任务

| 日期 | 任务 | 交付物 | 优先级 | 状态 |
|------|------|--------|--------|------|
| D15 | **定量评估**<br>用 OmniDocBench 子集测 Text ED / TEDS / CDM<br>与 MinerU2.5-Pro 基线对比<br>产出可视化报告（雷达图/柱状图） | 评估报告 PDF/HTML | 🔥 HIGH | 🔴 待办 |
| D16 | **定性评估 + Bad Case 修复**<br>人工审查 ≥50 页随机采样输出<br>按错误类型分类（文本/表格/公式/版面/阅读顺序）<br>补充最难 case 进入训练集进行第二轮回溯训练 | Bad Case 分析表 | 🔥 HIGH | 🔴 待办 |
| D17 | **vLLM 部署**<br>`swift deploy --infer_backend vllm`<br>`curl` 调用 REST API 验收<br>压测：吞吐量（req/s）和延迟（P50/P95） | 性能报告 | 🔥 HIGH | 🔴 待办 |
| D18 | **集成 perception-agent**<br>实现 `MinerUDocumentPerceiver`（继承 BasePerceptor）<br>单元测试：mock 图片 → Markdown 输出<br>确认 JanusAgent 管线能正常对接 | PR / commit | 🔥 HIGH | 🔴 待办 |

### 验收条件
- [ ] Text ED ≤ 0.10 或相对基线不退化
- [ ] vLLM API 响应时间 P95 < 3s
- [ ] perception-agent 集成测试绿

---

# 🎯 OKR-03：8月下半月（预留） — 深度优化与扩展

**Objective**: 在基础管线上叠加强化学习、数据引擎、长文处理等进阶能力。

| Key Result | 衡量标准 |
|---|---|
| KR-3.1 | 建立数据飞轮：Bad Case → 合成数据 → 重训闭环 |
| KR-3.2 | 模型在复杂版面（多栏、旋转表格、密集公式）上的指标突破基线 |
| KR-3.3 | 跑通 Megatron 分布式训练（如 4 卡以上） |

> 此 OKR 为预留空间，具体任务取决于前两个 OKR 的实际进展。

---

# 📊 进度快照

## 整体进度

```
OKR-01  ░░░░░░░░░░  0%
  ├─ 需求-01-1 环境与模型验证   □□□□ 0/4 subtasks
  └─ 需求-01-2 项目脚手架搭建   □□□□ 0/4 subtasks

OKR-02  ░░░░░░░░░░  0%
  ├─ 需求-02-1 首次 LoRA 微调   □□□ 0/3 subtasks
  ├─ 需求-02-2 超参数调优实验   □□□□ 0/4 subtasks
  ├─ 需求-02-3 进阶训练探索     □□ 0/2 subtasks
  └─ 需求-02-4 评估+部署        □□□□ 0/4 subtasks

OKR-03  ░░░░░░░░░░  （预留）
```

## 当前焦点

> 🔥 **今明两天优先做的事**:
> 1. 读论文，理解 MinerU2.5 的数据流程
> 2. `test_mineru_model.py --tiny` 跑通推理
> 3. 安装 ms-swift，跑通 `ocr.sh`

---

# 🔄 沟通约定

| 事项 | 约定 |
|------|------|
| **每日站会** | 每天早上更新任务状态（🔴🟡🟢） |
| **周报** | 每周日晚上总结本周需求进度 |
| **Blockers** | 立即提出，不积压到每日站会 |
| **决策记录** | 每次实验的超参和数据变更记入 `finetune/experiments/` 下的 ADR 文件 |

---

*创建于: 2026-07-09*
*下一版本更新: 随项目进展迭代*
