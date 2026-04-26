# 4 种芯片流水线模板重建工作空间

## 任务
基于 E:\work\Quantumchipdesin 中的真实芯片设计资料，重建 4 种芯片的多 Agent 协同流水线模板。

## 已完成
- 真实设计资料已注册到 QEDA 知识库（chip_real_designs.py）
- SPECS 中已有：1bit_real, 2bit_real, 20bit_ct20q, 105bit_real
- 新工具 qeda_real_design 已注册到 Hands

## 真实设计资料索引
- chip_real_designs.py: E:\work\QuantaMind\quantamind\server\chip_real_designs.py
- 包含 ALL_REAL_DESIGNS 字典，5 个设计

## 4 种流水线模板需求

### 1. 单比特流水线 (1bit_standard)
- 来源：E:\work\Quantumchipdesin\单比特\1bitV2.00\
- 参数：5 qubit (Q1-Q5)，全部 4.5GHz，谐振腔 7.22-7.35GHz
- Q3D 电容矩阵已有
- 阶段：设计→Q3D仿真→EPR分析→GDS导出→工艺文档生成

### 2. 双比特可调耦合流水线 (2bit_coupler)
- 来源：E:\work\Quantumchipdesin\双比特\2bits_coupler_V2_00\
- 参数：Q1=4.69G, Q2=5.204G, T1=7.123G (coupler), Q3=4.684G, Q4=5.204G, T2=7.123G
- 10mm x 10mm, 有完整 Python 版图代码 (250KB)
- 阶段：参数设计→版图生成(layout_2bits_coupler_V2_00.py)→Q3D仿真→谐振腔拟合→能级计算→GDS导出→工艺文档

### 3. 20比特 CT20Q 流水线 (20bit_tunable_coupler)
- 来源：E:\work\Quantumchipdesin\CT20Q\ + E:\work\QuantaMind\docs\QEDA\20比特设计方案.docx
- 12.5mm x 12.5mm, 20 qubits 1D chain, 19 couplers
- Qodd=5.152GHz, Qeven=4.650GHz, coupler=6.844GHz
- 有 V2.01 和 V3.00 两版 GDS zip
- 阶段：频率规划→版图设计→Q3D仿真→EPR分析→HFSS本征模→噪声预算→诊断→GDS导出→HFSS项目→工艺文档→封装设计

### 4. 105比特 FT105Q 流水线 (105bit_tunable_coupler)
- 来源：E:\work\Quantumchipdesin\105比特\ + E:\work\QuantaMind\docs\QEDA\105比特设计方案.docx
- GDS: 18 cells, 10 layers, 95,238 shapes
- 阶段：频率规划→版图设计→Q3D→EPR→HFSS→噪声→诊断→GDS→HFSS→工艺→封装→测试

## 需要修改的文件
- Gateway (gateway.py): 添加/修改流水线模板定义和运行函数
- 前端 (index.html): 流水线模板列表页面
- chip_designer_metal.py: 芯片设计函数

## 当前流水线模板位置
- gateway.py 中的 template_runners 字典
- _run_20bit_pipeline, _run_100bit_pipeline, _run_105bit_pipeline 函数
