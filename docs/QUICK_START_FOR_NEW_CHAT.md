# QuantaMind 新对话快速启动指南

本文件帮助新对话快速恢复上下文。根据你要做的事情，选择对应的指令。

---

## 芯片设计改进
让 QuantaMind 生成的版图达到团队真实设计水平（24,888 shapes）。

**新对话贴这句：**
```
请读取 E:\work\QuantaMind\docs\paper_workspace\HANDOVER_CHIP_DESIGN.md，按照方案 A+B 组合，修改版图代码让 QuantaMind 能直接调用团队的 twenty_qubits_tunable_coupler_layout() 生成工业级 GDS。
```

---

## 论文写作（第二篇：多智能体协同框架）
基于 5 组协同实验写 20+ 页论文。

**新对话贴这句：**
```
请读取 E:\work\QuantaMind\docs\paper_workspace\README_FRAMEWORK_PAPER.md，基于里面的实验数据和材料，写一篇 20+ 页的博士水平英文学术论文，输出 Word 格式。
```

---

## QuantaMind 软件开发（前端/后端/新功能）
继续开发 QuantaMind 系统（Web UI、Gateway、Agent、工具等）。

**新对话贴这句：**
```
请读取 E:\work\QuantaMind\docs\QuantaMind量智大脑详细设计说明书.md 的前 200 行了解系统架构。
QuantaMind 项目代码在 E:\work\QuantaMind\，Gateway 在 quantamind\server\gateway.py，
前端在 quantamind\client\web\index.html，Orchestrator 在 quantamind\agents\orchestrator.py。
我需要 [在这里写你要做的具体功能]。
```

---

## 20 比特版图精修（对标参考图）
继续把 GDS 版图做得更像参考图。

**新对话贴这句：**
```
请读取 E:\work\QuantaMind\quantamind\server\gds_generator.py 中的 generate_reference_20bit_gds 函数，
参考图在 C:\Users\Huawei\.cursor\projects\e-work-EDA-Q-main\assets\ 目录下。
继续做"逐根线、逐个器件"的版图复刻。
```

---

## 日常使用和调试
Gateway 启动/重启、KLayout 打开 GDS、查看状态等。

**直接问就行，不需要特殊指令。常用信息：**
- Gateway 地址：http://127.0.0.1:18789
- 守护进程：自动在后台运行，崩溃自恢复
- 数据目录：D:\.quantamind\（C盘有符号链接）
- 芯片 GDS：D:\.quantamind\outputs\chip_designs\
- KLayout：C:\Program Files (x86)\KLayout\klayout_app.exe
- Ansys：D:\ANSYS Inc\ANSYS Student\v252\AnsysEM\

---

## 关键文件索引
| 文件 | 内容 |
|------|------|
| E:\work\QuantaMind\docs\paper_workspace\HANDOVER_CHIP_DESIGN.md | 芯片设计改进完整交接 |
| E:\work\QuantaMind\docs\paper_workspace\README_FRAMEWORK_PAPER.md | 第二篇论文材料 |
| E:\work\QuantaMind\docs\paper_workspace\README_FOR_NEW_CHAT.md | 第一篇论文材料 |
| E:\work\QuantaMind\docs\QuantaMind量智大脑详细设计说明书.md | 系统架构设计文档 |
| E:\work\QuantaMind\quantamind\server\gateway.py | Gateway 主文件 |
| E:\work\QuantaMind\quantamind\client\web\index.html | Web 前端 |
| E:\work\QuantaMind\quantamind\agents\orchestrator.py | Agent 编排器 |
| E:\work\QuantaMind\quantamind\server\layout_CT20QV2_01.py | 团队真实 20 比特版图代码 (5088 行) |
| E:\work\QuantaMind\quantamind\server\CT20QV2_01.json | 20 比特参数 JSON (253 组件) |
| E:\work\QuantaMind\quantamind\server\real_chip_builder.py | 真实芯片 GDS 部署工具 |
| E:\work\QuantaMind\quantamind\server\hands_theorist.py | 理论物理学家 Agent (M0-M8) |
| E:\work\QuantaMind\quantamind\server\hands_simulation.py | 仿真引擎 (HFSS/Q3D) |
