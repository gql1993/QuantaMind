import { getJson, postJson } from './client'

export type AuthUser = {
  user_id: string
  display_name: string
  role_id: string
  role_label: string
}

export type LoginResponse = {
  success: boolean
  data: {
    access_token: string
    token_type: 'bearer'
    user: AuthUser
  }
  error: null
}

export type CurrentUserResponse = {
  success: boolean
  data: AuthUser
  error: null
}

export function loginWithRole(roleId: string) {
  return postJson<LoginResponse>('/api/v1/auth/login', { role_id: roleId })
}

export function fetchCurrentUser() {
  return getJson<CurrentUserResponse>('/api/v1/auth/me')
}
