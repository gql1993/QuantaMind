# Phase 14 实施草案（Draft 0.1）

## 目标

在 Phase 13 收口基础上，补齐 QuantaMind 2.0 剩余“骨架模块”，把 V2 从“可运行实验线”推进到“可配置、可扩展、可落地迁移”的工程化阶段。

## Phase 14 拆分

1. **Phase 14-1 配置统一层（config）**
   - 建立 `AppSettings + FeatureFlags + RuntimeLimits + ProviderSettings`
   - 网关支持注入 settings 并提供只读配置摘要
2. **Phase 14-2 agents 能力画像首版**
   - 落地 `agents/registry.py`、`agents/base.py`、`agents/policies.py`
   - 将角色从“名称”升级为“能力声明（工具/上下文/artifact 输出）”
3. **Phase 14-3 client/shared 共享状态契约**
   - 抽取 Run/Task/Artifact 的前端共享数据结构
   - 为 Web 与 Desktop 保持一致渲染模型
4. **Phase 14-4 gateway 路由模块化**
   - 将 `core/gateway/app.py` 拆分为 `routes_*`
   - 保持现有路径兼容，降低单文件复杂度

## 本批第一项（14-1）验收标准

- `quantamind_v2/config/` 目录可独立导入；
- `create_app(settings=...)` 生效；
- `GET /api/v2/config/summary` 返回当前运行配置；
- 至少包含覆盖 settings 的单测与 gateway 接口测试。
