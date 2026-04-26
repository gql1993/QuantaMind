# QuantaMind 芯片设计改进交接文档

## 核心目标
让 QuantaMind 生成的芯片版图达到团队真实设计的水平（24,888 shapes vs 当前 619 shapes）。
方法：直接调用团队的 5088 行版图代码和自定义组件库，而不是用 gdstk 画简化几何。

## 当前状态

### 已完成
1. `user_components` 25 个文件已安装到 Qiskit Metal 目录
   - 路径：`C:\Users\Huawei\AppData\Local\Programs\Python\Python311\Lib\site-packages\qiskit_metal\qlibrary\user_components\`
   - 核心组件均可导入：my_qcomponent, stable_meander, airbridge, save_load, reader
   - `__init__.py` 已改为安全导入模式（try/except）

2. 团队版图代码已复制到 QuantaMind
   - `E:\work\QuantaMind\quantamind\server\layout_CT20QV2_01.py` (5088 行, 250KB)
   - `E:\work\QuantaMind\quantamind\server\CT20QV2_01.json` (253 个组件参数)

3. `twenty_qubits_tunable_coupler_layout()` 已测试
   - 成功创建了 20 个 meander + 比特 + 耦合器 + 谐振腔
   - 在 `readout_line_21` 的 RoutePathfinder 处崩溃（AttributeError: 'NoneType' object has no attribute 'coords'）
   - 后续 readout_line_30, readout_line_31 也有同样问题
   - 进程最终因内存异常退出（exit code -1073741819）

4. 真实 GDS 文件已部署到 `D:\.quantamind\outputs\chip_designs\`
   - 1bit: 3.27 MB, 5122 shapes
   - 2bit: 0.29 MB, 366 shapes
   - 20bit: 9.16 MB, 24888 shapes
   - 105bit: 55.83 MB, 95238 shapes

5. `real_chip_builder.py` 当前策略是复制已有 GDS，不运行版图代码

### 关键已知问题
1. **gdspy 未安装**（需要 C++ 编译器，pip install gdspy 失败）
   - 影响：cell.py, indium_generator.py, indium_process.py, writer.py 不可用
   - 不影响核心组件：my_qcomponent, stable_meander, airbridge, cpw, save_load, reader

2. **RoutePathfinder 在 offscreen 模式崩溃**
   - 原因：A* 寻路在 boundary.geometry.exterior[0].coords 处遇到 NoneType
   - 可能因为 offscreen 模式下某些几何计算不完整
   - 上次尝试的 monkey-patch（跳过失败走线）方案只部分有效

3. **MetalGUI 在 offscreen 模式有很多 WARNING**
   - QFontDatabase 找不到字体目录
   - propagateSizeHints/raise 不支持
   - 但不影响功能，版图仍能生成

## 改进方案

### 方案 A：修改版图代码支持分步导出（推荐）
在 `twenty_qubits_tunable_coupler_layout()` 中：
1. 在所有 meander 创建完成后（约第 3150 行，readout_line 开始前）插入中间 GDS 导出
2. 把 readout_line 的 RoutePathfinder 全部包在 try/except 中
3. 最终导出完整版 GDS（即使部分走线失败）

具体修改位置：
- 第 2845 行后：MetalGUI 创建后，设计开始
- 第 3100-3150 行左右：20 个 meander 创建完成
- 第 3373 行：readout_line_21 开始（第一个失败点）
- 第 3930 行：函数返回 `return design, gui`

### 方案 B：跳过 MetalGUI
真实版图代码的 `gui = MetalGUI(design)` 只是用于可视化，组件创建不依赖 GUI。
可以在导入时 monkey-patch MetalGUI 为一个空壳类，避免所有 Qt 相关问题。

### 方案 C：直接使用团队已生成的 GDS + 仿真数据
当前已实现（real_chip_builder.py）。但不够——因为用户希望 QuantaMind 能"设计"而不只是"复制"。

### 推荐：方案 A + B 组合
1. Monkey-patch MetalGUI 为 NoopGUI
2. 调用 twenty_qubits_tunable_coupler_layout(parameter_file_path=json_path)
3. RoutePathfinder 全部 try/except
4. 完成后导出 GDS

## 真实设计的关键技术点（QuantaMind 应学习的）

### 1. 自定义 Xmon 组件 (my_qcomponent.py)
- 不是用 TransmonPocket/TransmonCross
- 用团队自研的 Xmon_round（圆角十字臂）
- 参数包括：cross_width, cross_length, cross_gap, connection_pads（带 arm_length, arm_width, coupling_length）

### 2. 可调耦合器组件
- 团队自研的 TunableCoupler
- 参数：c_width, l_width, c_height, c_gap, m_width, fl_length, fl_width, fl_ground, fillet

### 3. CoupledLineTee 谐振腔耦合
- 精确控制 coupling_length（120-200um 不等，影响谐振腔 Qe）
- coupling_space = 3um
- prime_width/gap = 10um/5um

### 4. StableRouteMeander
- 团队自研，解决原生 RouteMeander 的 fillet 崩溃
- 支持 jog（折弯）和 anchor（锚点）

### 5. AirbridgeGenerator
- 在 CPW 走线上自动生成空气桥
- 参数：edge_space, bridge_spacing 等

### 6. 48 个 LaunchpadWirebond
- 四边各 12 个，精确坐标由 JSON 控制
- pad_width=245um, pad_height=245um, pad_gap=100um, lead_length=176um

### 7. 工艺层定义
- layer 0: 接地平面（CPW 主层）
- layer 11: JJ 层 1（约瑟夫森结下电极）
- layer 12: JJ 层 2（约瑟夫森结上电极）
- layer 14: 空气桥层
- layer 31: 衬底标记层
- layer 32: 对准/切割标记层

## 文件路径速查
- 版图代码：E:\work\QuantaMind\quantamind\server\layout_CT20QV2_01.py
- 参数 JSON：E:\work\QuantaMind\quantamind\server\CT20QV2_01.json
- 真实 GDS 源：E:\work\Quantumchipdesin\ (1bit/2bit/CT20Q/105bit)
- 输出目录：D:\.quantamind\outputs\chip_designs\
- user_components：已安装到 site-packages\qiskit_metal\qlibrary\user_components\
- Qiskit Metal GDS 渲染器已修复：pandas append→concat, positive_mask try/except
- QuantaMind 数据根目录：D:\.quantamind（C盘符号链接）
- Gateway 配置：E:\work\QuantaMind\quantamind\config.py（DEFAULT_ROOT 已 resolve()）
- 守护进程：E:\work\QuantaMind\run_gateway_daemon.py（后台常驻+自恢复）
- Ansys 安装：D:\ANSYS Inc\ANSYS Student\v252\AnsysEM\（已检测）
- KLayout：C:\Program Files (x86)\KLayout\klayout_app.exe（已安装）

## 新对话的指令
```
请读取 E:\work\QuantaMind\docs\paper_workspace\HANDOVER_CHIP_DESIGN.md，
按照方案 A+B 组合，修改版图代码让 QuantaMind 能直接调用团队的
twenty_qubits_tunable_coupler_layout() 生成工业级 GDS。
```
