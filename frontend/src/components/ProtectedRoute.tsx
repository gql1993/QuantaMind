import type { ReactNode } from 'react'

import { useCurrentPermissions } from '../hooks/useCurrentPermissions'

type ProtectedRouteProps = {
  requiredPermission: string
  title?: string
  children: ReactNode
}

export function ProtectedRoute({ requiredPermission, title = '当前角色无权访问该页面', children }: ProtectedRouteProps) {
  const { permissions, permissionError, hasPermission } = useCurrentPermissions()

  if (permissionError) {
    return <div className="error-banner">权限校验失败：{permissionError}</div>
  }

  if (!permissions) {
    return <div className="info-banner">正在校验访问权限...</div>
  }

  if (!hasPermission(requiredPermission)) {
    return (
      <section className="panel access-denied">
        <span className="card-kicker">Access Denied</span>
        <h2>{title}</h2>
        <p>请切换到具备后台管理权限的角色，或联系管理员开通 `{requiredPermission}` 权限。</p>
      </section>
    )
  }

  return children
}
