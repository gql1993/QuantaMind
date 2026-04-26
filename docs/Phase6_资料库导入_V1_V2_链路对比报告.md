# Phase 6：资料库导入 V1/V2 链路对比报告

更新日期：2026-04-09

## 1. 目标

将「资料库导入」从 V1 迁入 V2，并确认已接入 V2 的 Run/Task/Artifact 统一链路。

## 2. V1 现状（基线）

- 入口：`POST /api/v1/library/upload`
- 查询：
  - `GET /api/v1/library/files`
  - `GET /api/v1/library/files/{file_id}`
  - `GET /api/v1/library/stats`
- 特点：
  - 上传后在 V1 内部直接解析/索引
  - 任务状态通过 `state_store` 维护（library-ingest-jobs）
  - 结果与 Run/Artifact 链路是并行关系，不是统一控制平面

## 3. V2 已落地链路

- 新增接口：
  - `POST /api/v2/library/upload`
  - `GET /api/v2/library/files`
  - `GET /api/v2/library/files/{file_id}`
  - `GET /api/v2/library/stats`
- 内部执行路径：
  1. 上传后创建 `import_run`
  2. 提交 `library_ingest:*` 后台 task（`/api/v2/tasks` 可观测）
  3. ingest 完成后写入 `library_ingest_report` artifact
  4. artifact 挂载到 run（`/api/v2/runs/{run_id}/artifacts`）
- 关键收益：
  - 资料库导入已进入 V2 统一 Run/Task/Artifact 链路
  - 可直接在 Run Console、Task Center、Artifact Viewer 中追踪

## 4. 验证结果

- 自动化测试新增：
  - `tests/v2/test_gateway_library.py`
- 覆盖点：
  - 上传 -> import_run + task 创建
  - task 完成 -> run 完成 + artifact 生成
  - files/list/search/stats 可用

## 5. 差距与下一步

- 当前 V2 资料库导入为最小可用实现（内存 service + 轻量解析）
- 下一步（Phase 6）建议：
  1. 迁入一条标准流水线到 V2（含对比报告）
  2. 把 V1 的复杂解析与索引策略逐步移植到 V2 service
  3. 输出稳定性与可观测性对比指标（耗时、失败率、可追踪字段）
