# Phase 15 实施草案（Draft 0.1）

## 目标

在 Phase 14 的模块化基础上，推进“客户端工作台深化”，让 Web/Desktop 不只是能看状态，而是具备可配置、可恢复、可复用的工作区能力。

## Phase 15 拆分

1. **Phase 15-1 客户端工作区布局管理**
   - 建立 `client/shared` 布局契约与存储（web/desktop）
   - 网关提供布局查询、创建、激活、快照接口
2. **Phase 15-2 Desktop 交互深化**
   - 桌面壳支持 active layout 渲染与 panel 级刷新策略
3. **Phase 15-3 Web/Desktop 偏好同步**
   - 用户级布局偏好与常用快捷栏同步
4. **Phase 15-4 工作台恢复点**
   - 保存/恢复 run/task/artifact 定位上下文

## 本批第一项（15-1）验收标准

- `client/shared` 有统一布局模型与默认布局；
- `api/v2/client/workspace/*` 提供布局增删查激活与快照；
- 保持现有 `/api/v2/client/shared/state` 兼容；
- 增加 gateway 与 shared 层测试覆盖。
