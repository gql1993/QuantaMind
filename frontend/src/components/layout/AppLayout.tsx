import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import { fetchCurrentUserPermissions, type CurrentUserPermissions, type PermissionMenuItem } from '../../api/permissions'

const fallbackNavItems: PermissionMenuItem[] = [
  { to: '/workspace', label: '工作台总览', end: true },
  { to: '/workspace/roles', label: '角色首页' },
  { to: '/workspace/ai', label: 'AI 工作台' },
  { to: '/workspace/tasks', label: '我的任务' },
  { to: '/workspace/artifacts', label: '产物中心' },
  { to: '/workspace/agents', label: '智能体' },
  { to: '/admin/runs', label: '后台 Run 控制台' },
  { to: '/admin/system', label: '后台系统监控' },
].map((item) => ({
  key: item.to,
  label: item.label,
  path: item.to,
  scope: item.to.startsWith('/admin') ? 'admin' : 'workspace',
  end: item.end,
}))

export function AppLayout() {
  const [permissions, setPermissions] = useState<CurrentUserPermissions | null>(null)
  const [permissionError, setPermissionError] = useState<string | null>(null)
  const navItems = permissions?.menus ?? fallbackNavItems

  useEffect(() => {
    let ignore = false

    fetchCurrentUserPermissions()
      .then((response) => {
        if (ignore) {
          return
        }
        setPermissions(response.data)
        setPermissionError(null)
      })
      .catch((error: unknown) => {
        if (ignore) {
          return
        }
        setPermissionError(error instanceof Error ? error.message : 'Unknown permission error')
      })

    return () => {
      ignore = true
    }
  }, [])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">QuantaMind</div>
        <div className="user-card">
          <span>{permissions?.user.role_label ?? '权限加载中'}</span>
          <strong>{permissions?.user.display_name ?? 'Demo User'}</strong>
          {permissionError && <small>使用本地菜单：{permissionError}</small>}
        </div>
        <nav>
          {navItems.map((item) => (
            <NavLink
              key={item.key}
              to={item.path}
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
