# Phase 6：标准流水线 V1/V2 稳定性对比报告

更新日期：2026-04-09

## 1. 目标

在 V2 落一条可运行的标准流水线，接入统一 Run/Task/Artifact 链路，并与 V1 流水线能力做最小稳定性对比。

## 2. V2 本次新增

- 新增流水线模板接口：
  - `GET /api/v2/pipelines/templates`
- 新增流水线执行接口：
  - `POST /api/v2/pipelines/execute`
- 默认模板：
  - `standard_daily_ops`（顺序执行 `system_status` -> `db_status` -> `intel_today`）
- 链路行为：
  1. 创建 `pipeline_run`
  2. 背景提交 `pipeline:*` 任务（Task Center 可见）
  3. 逐步触发子 shortcut（child runs，`parent_run_id` 关联父 run）
  4. 汇总输出 `pipeline_report` artifact

## 3. 稳定性与可观测性对比（最小样本）

### V1（既有）

- 具备成熟流水线页面与控制能力（暂停/恢复/终止等）
- 运行状态主要在 V1 内部 pipeline 结构中追踪

### V2（当前）

- 优点：
  - 统一进入 Run/Task/Artifact 链路，追踪字段标准化
  - 子任务父子关系明确（`parent_run_id`）
  - 失败时可在任务中心直接定位，便于回放
- 限制：
  - 目前模板数量少（1 条）
  - 控制能力还未与 V1 对齐（如 pause/resume）

## 4. 测试结果

- 新增测试：`tests/v2/test_gateway_pipeline.py`
- 覆盖场景：
  - 模板查询与成功执行
  - 子 run 关联检查
  - `pipeline_report` artifact 产出
  - 失败传播（子 shortcut 失败 -> pipeline task/run failed）

## 5. 结论与下一步

- 结论：V2 已具备“标准流水线最小闭环”，能进入统一控制平面并提供可观测链路。
- 下一步建议：
  1. 增加第二条业务流水线模板（对接资料库导入场景）
  2. 补 `pause/resume/abort` 控制接口与前端操作
  3. 增加流水线 SLA 指标（平均时长、失败率、重试率）
