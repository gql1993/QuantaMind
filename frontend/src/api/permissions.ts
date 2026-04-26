import { getJson } from './client'

export type PermissionMenuItem = {
  key: string
  label: string
  path: string
  scope: 'workspace' | 'admin'
  end?: boolean
}

export type CurrentUserPermissions = {
  user: {
    user_id: string
    display_name: string
    role_id: string
    role_label: string
  }
  permissions: string[]
  menus: PermissionMenuItem[]
  restricted_menus: PermissionMenuItem[]
}

export type CurrentUserPermissionsResponse = {
  success: boolean
  data: CurrentUserPermissions
  error: null
}

export function fetchCurrentUserPermissions() {
  return getJson<CurrentUserPermissionsResponse>('/api/v1/permissions/me')
}
