import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import './App.css'
import { AppLayout } from './components/layout/AppLayout'
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
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/workspace" replace />} />
          <Route path="/workspace" element={<OverviewPage />} />
          <Route path="/workspace/roles" element={<RoleWorkspacePage />} />
          <Route path="/workspace/ai" element={<AiWorkbenchPage />} />
          <Route path="/workspace/tasks" element={<RunsPage />} />
          <Route path="/workspace/tasks/:runId" element={<RunDetailPage />} />
          <Route path="/workspace/artifacts" element={<ArtifactsPage />} />
          <Route path="/workspace/artifacts/:artifactId" element={<ArtifactDetailPage />} />
          <Route path="/workspace/data" element={<DataCenterPage />} />
          <Route path="/workspace/knowledge" element={<KnowledgeMemoryPage />} />
          <Route path="/workspace/agents" element={<AgentsPage />} />
          <Route path="/workspace/agents/:agentId" element={<AgentDetailPage />} />
          <Route path="/admin/agents" element={<AdminAgentsPage />} />
          <Route path="/admin/audit" element={<AdminAuditPage />} />
          <Route path="/admin/runs" element={<RunsPage admin />} />
          <Route path="/admin/runs/:runId" element={<RunDetailPage admin />} />
          <Route path="/admin/system" element={<AdminSystemPage />} />
          <Route path="*" element={<Navigate to="/workspace" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
