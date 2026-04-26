export type RoleProfile = {
  roleId: string
  name: string
  description: string
  defaultEntry: string
  primaryAgent: string
  responsibilities: string[]
  quickActions: Array<{
    label: string
    path: string
  }>
  visibleMenus: string[]
  restrictedMenus: string[]
}

export const roleProfiles: RoleProfile[] = [
  {
    roleId: 'chip-designer',
    name: '芯片设计人员',
    description: '聚焦芯片设计任务、仿真分析、设计风险识别和产物沉淀。',
    defaultEntry: '/workspace/tasks',
    primaryAgent: 'design_specialist',
    responsibilities: ['设计方案分析', '仿真任务跟踪', '设计风险复核', '设计产物归档'],
    quickActions: [
      { label: '查看设计任务', path: '/workspace/tasks' },
      { label: '发起 AI 分析', path: '/workspace/ai' },
      { label: '查看设计产物', path: '/workspace/artifacts' },
    ],
    visibleMenus: ['工作台总览', '角色首页', 'AI 工作台', '我的任务', '产物中心', '智能体'],
    restrictedMenus: ['后台 Run 控制台', '后台系统监控', '权限策略', '审计日志'],
  },
  {
    roleId: 'test-engineer',
    name: '测控人员',
    description: '围绕测试计划、校准任务、设备状态和异常闭环开展工作。',
    defaultEntry: '/workspace/tasks',
    primaryAgent: 'calibration_agent',
    responsibilities: ['测试任务执行', '校准结果复核', '异常数据上报', '测试报告生成'],
    quickActions: [
      { label: '查看测控任务', path: '/workspace/tasks' },
      { label: '查看运行事件', path: '/admin/runs' },
      { label: '查看产物报告', path: '/workspace/artifacts' },
    ],
    visibleMenus: ['工作台总览', '角色首页', '我的任务', '产物中心', '智能体'],
    restrictedMenus: ['后台系统监控', '权限策略', '模型配置', '审计日志'],
  },
  {
    roleId: 'data-analyst',
    name: '数据分析人员',
    description: '负责数据同步、指标分析、摘要产物和跨域洞察输出。',
    defaultEntry: '/workspace/artifacts',
    primaryAgent: 'data_analyst',
    responsibilities: ['数据同步检查', '指标看板分析', '异常趋势识别', '分析摘要输出'],
    quickActions: [
      { label: '查看数据产物', path: '/workspace/artifacts' },
      { label: '新建分析 Run', path: '/workspace/tasks' },
      { label: '调用 AI 工作台', path: '/workspace/ai' },
    ],
    visibleMenus: ['工作台总览', '角色首页', 'AI 工作台', '我的任务', '产物中心', '智能体'],
    restrictedMenus: ['后台系统监控', 'Agent 启停', '权限策略', '审计日志'],
  },
  {
    roleId: 'project-manager',
    name: '项目经理',
    description: '关注项目进度、任务风险、跨角色协作和阶段性汇报。',
    defaultEntry: '/workspace',
    primaryAgent: 'orchestrator',
    responsibilities: ['任务进度跟踪', '风险与阻塞识别', '跨角色协同', '阶段汇报汇总'],
    quickActions: [
      { label: '查看总体工作台', path: '/workspace' },
      { label: '查看全部任务', path: '/workspace/tasks' },
      { label: '查看产物中心', path: '/workspace/artifacts' },
    ],
    visibleMenus: ['工作台总览', '角色首页', 'AI 工作台', '我的任务', '产物中心', '智能体'],
    restrictedMenus: ['系统配置', '权限策略', '密钥管理', '底层运行时配置'],
  },
]
