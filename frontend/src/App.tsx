import { BrowserRouter, HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import type { ReactNode } from 'react'

import './App.css'
import { AppLayout } from './components/layout/AppLayout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AgentDetailPage } from './pages/AgentDetailPage'
import { AgentsPage } from './pages/AgentsPage'
import { AdminAgentsPage } from './pages/AdminAgentsPage'
import { AdminAuditPage } from './pages/AdminAuditPage'
import { AdminSystemPage } from './pages/AdminSystemPage'
import { AiWorkbenchPage } from './pages/AiWorkbenchPage'
import { ArtifactDetailPage } from './pages/ArtifactDetailPage'
import { ArtifactsPage } from './pages/ArtifactsPage'
import { DataCenterPage } from './pages/DataCenterPage'
import { KnowledgeMemoryPage } from './pages/KnowledgeMemoryPage'
import { OverviewPage } from './pages/OverviewPage'
import { RoleWorkspacePage } from './pages/RoleWorkspacePage'
import { RunDetailPage } from './pages/RunDetailPage'
import { RunsPage } from './pages/RunsPage'

function App() {
  const Router = window.electronAPI ? HashRouter : BrowserRouter
  const requireAdmin = (page: ReactNode) => (
    <ProtectedRoute requiredPermission="admin:read" title="当前角色无权访问该后台页面">
      {page}
    </ProtectedRoute>
  )
  const requirePermission = (permission: string, page: ReactNode) => (
    <ProtectedRoute requiredPermission={permission}>{page}</ProtectedRoute>
  )

  return (
    <Router>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/workspace" replace />} />
          <Route path="/workspace" element={<OverviewPage />} />
          <Route path="/workspace/roles" element={<RoleWorkspacePage />} />
          <Route path="/workspace/ai" element={requirePermission('chat:use', <AiWorkbenchPage />)} />
          <Route path="/workspace/tasks" element={requirePermission('run:read', <RunsPage />)} />
          <Route path="/workspace/tasks/:runId" element={requirePermission('run:read', <RunDetailPage />)} />
          <Route path="/workspace/artifacts" element={requirePermission('artifact:read', <ArtifactsPage />)} />
          <Route
            path="/workspace/artifacts/:artifactId"
            element={requirePermission('artifact:read', <ArtifactDetailPage />)}
          />
          <Route path="/workspace/data" element={requirePermission('data:read', <DataCenterPage />)} />
          <Route path="/workspace/knowledge" element={requirePermission('knowledge:read', <KnowledgeMemoryPage />)} />
          <Route path="/workspace/agents" element={requirePermission('agent:read', <AgentsPage />)} />
          <Route path="/workspace/agents/:agentId" element={requirePermission('agent:read', <AgentDetailPage />)} />
          <Route path="/admin/agents" element={requireAdmin(<AdminAgentsPage />)} />
          <Route path="/admin/audit" element={requireAdmin(<AdminAuditPage />)} />
          <Route path="/admin/runs" element={requireAdmin(<RunsPage admin />)} />
          <Route path="/admin/runs/:runId" element={requireAdmin(<RunDetailPage admin />)} />
          <Route path="/admin/system" element={requireAdmin(<AdminSystemPage />)} />
          <Route path="*" element={<Navigate to="/workspace" replace />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
