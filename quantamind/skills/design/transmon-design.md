---
name: transmon-quantum-bit-design
version: 1.0.0
trigger: "设计transmon|创建量子比特|transmon design"
tools: [echo, search_knowledge]
agents: [designer_agent]
domain: quantum_chip_design
---

# Transmon 量子比特设计技能

当用户请求设计 Transmon 类型量子比特时触发。

## 执行流程

### Step 1: 需求澄清
向用户确认：目标频率范围（默认 4.5–5.5 GHz）、非谐性目标、耦合方式、读出方式。

### Step 2: 理论计算
基于目标频率反算 EJ/EC 比例，估算约瑟夫森结面积。

### Step 3: 几何参数生成
结合频率预测（后续接专家模型），输出 pad_width、pad_gap、jj_area 等。

### Step 4: 版图生成
调用 Q-EDA 创建设计并放置 Transmon 组件（Phase 2 对接）。

### Step 5: 设计检查
DRC 与设计规则检查（Phase 2 对接）。

### Step 6: 知识沉淀
将设计参数与决策记录到项目记忆。
