# Phase 19 实施草案（Draft 0.1）

## 目标

在 Phase 18 文件持久化能力基础上，推进数据库化落地，逐步完成从“文件主存储”到“数据库主存储”的平滑迁移。

## 拆分建议

1. **Phase 19-1 Dual-write 基线**
   - 保持文件存储为主读
   - 新增 SQLite 同步写作为次写
   - 提供双写健康信息
2. **Phase 19-2 对账与一致性校验**
   - 建立文件与数据库的行数/时间窗口对账
   - 暴露差异检查接口
3. **Phase 19-3 Cutover 预演**
   - 增加数据库优先读开关
   - 提供回退到文件读路径

## 本批第一项（19-1）验收标准

- 可通过配置开关启用 dual-write；
- 冲突策略与审计事件可同时写入文件与 SQLite；
- 不影响现有查询路径与对外接口行为；
- 有自动化测试证明双写已生效。

## 19-2 落地记录（2026-04-12）

- 新增一致性对账能力：
  - 审计对账：窗口比对（`window_limit`）+ 差异统计 + 异常样本
  - 策略对账：profile 策略差异统计 + 异常样本
- 新增接口：
  - `GET /api/v2/coordination/persistence/consistency`
    - 输出 `reports.audit` / `reports.policy`
    - 提供 `difference_count`、`anomalies`、`status`
- 观测面板增强：
  - `GET /api/v2/coordination/persistence/dashboard` 在 dual-write 模式附带 `consistency`

## 19-3 落地记录（2026-04-12）

- 新增配置开关：
  - `coordination.database_read_preferred`（是否数据库优先读）
  - `coordination.database_read_fallback_to_file`（数据库读失败时是否回退文件）
- dual-write 读路径升级：
  - 审计读取与策略读取支持数据库优先；失败可自动回退文件
  - 健康报告附带最近读来源与最近回退原因
- 新增 cutover 演练接口：
  - `GET /api/v2/coordination/persistence/cutover/drill`
  - 支持 `simulate_secondary_failure=true` 模拟数据库读失败，验证回退策略
