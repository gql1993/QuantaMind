import { useState } from 'react'
import { Link } from 'react-router-dom'

import { roleProfiles } from '../config/roleProfiles'

export function RoleWorkspacePage() {
  const [activeRoleId, setActiveRoleId] = useState(roleProfiles[0].roleId)
  const activeRole = roleProfiles.find((role) => role.roleId === activeRoleId) ?? roleProfiles[0]

  return (
    <>
      <section className="role-hero">
        <div>
          <span className="card-kicker">Role Workspace</span>
          <h2>角色化前台首页</h2>
          <p>按员工角色切换默认入口、任务关注点和菜单可见范围，作为后续权限系统的前端占位。</p>
        </div>
      </section>

      <section className="role-tabs">
        {roleProfiles.map((role) => (
          <button
            type="button"
            key={role.roleId}
            className={role.roleId === activeRole.roleId ? 'active' : ''}
            onClick={() => setActiveRoleId(role.roleId)}
          >
            {role.name}
          </button>
        ))}
      </section>

      <section className="role-layout">
        <article className="panel role-main-card">
          <div className="panel-head">
            <div>
              <span className="card-kicker">{activeRole.roleId}</span>
              <h2>{activeRole.name}</h2>
            </div>
            <span className="badge completed">默认智能体：{activeRole.primaryAgent}</span>
          </div>
          <p>{activeRole.description}</p>

          <div className="role-section">
            <h3>核心职责</h3>
            <div className="role-duty-grid">
              {activeRole.responsibilities.map((item) => (
                <article key={item}>
                  <span>Responsibility</span>
                  <strong>{item}</strong>
                </article>
              ))}
            </div>
          </div>

          <div className="role-section">
            <h3>快捷入口</h3>
            <div className="quick-action-grid">
              {activeRole.quickActions.map((action) => (
                <Link to={action.path} key={action.label}>
                  {action.label}
                </Link>
              ))}
            </div>
          </div>
        </article>

        <aside className="panel permission-card">
          <div className="panel-head">
            <div>
              <span className="card-kicker">Permission Placeholder</span>
              <h2>菜单权限占位</h2>
            </div>
          </div>
          <div className="role-section">
            <h3>可见菜单</h3>
            <div className="tag-list allow">
              {activeRole.visibleMenus.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </div>
          <div className="role-section">
            <h3>受限菜单</h3>
            <div className="tag-list deny">
              {activeRole.restrictedMenus.map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          </div>
          <div className="info-banner">当前为前端占位配置，后续可替换为用户、角色、权限 API 返回结果。</div>
        </aside>
      </section>
    </>
  )
}
