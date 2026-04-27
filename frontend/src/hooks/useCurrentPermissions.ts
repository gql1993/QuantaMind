import { useEffect, useState } from 'react'

import { onAccessTokenChanged } from '../api/client'
import { fetchCurrentUserPermissions, type CurrentUserPermissions } from '../api/permissions'

export function useCurrentPermissions() {
  const [permissions, setPermissions] = useState<CurrentUserPermissions | null>(null)
  const [permissionError, setPermissionError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false

    function loadPermissions() {
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
    }

    loadPermissions()
    const unsubscribe = onAccessTokenChanged(loadPermissions)

    return () => {
      ignore = true
      unsubscribe()
    }
  }, [])

  function hasPermission(permission: string) {
    return permissions?.permissions.includes(permission) ?? false
  }

  return { permissions, permissionError, hasPermission }
}
