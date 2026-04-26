import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/workspace', label: '工作台总览', end: true },
  { to: '/workspace/ai', label: 'AI 工作台' },
  { to: '/workspace/tasks', label: '我的任务' },
  { to: '/workspace/artifacts', label: '产物中心' },
  { to: '/workspace/agents', label: '智能体' },
  { to: '/admin/runs', label: '后台 Run 控制台' },
  { to: '/admin/system', label: '后台系统监控' },
]

export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">QuantaMind</div>
        <nav>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Frontend / Backend Split</p>
            <h1>量智大脑分离式工作台</h1>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  )
}
