import { useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api.js'
import { AuthContext } from './context.js'

const TOKEN_STORAGE_KEY = 'recipe-share.access-token'
const USER_STORAGE_KEY = 'recipe-share.current-user'

function clearStoredAuth() {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(USER_STORAGE_KEY)
}

function getStoredAuth() {
  const accessToken = localStorage.getItem(TOKEN_STORAGE_KEY)
  const storedUser = localStorage.getItem(USER_STORAGE_KEY)

  if (!accessToken || !storedUser) {
    clearStoredAuth()
    return null
  }

  try {
    const user = JSON.parse(storedUser)
    if (!user || typeof user !== 'object' || !user.username) {
      clearStoredAuth()
      return null
    }
    return { accessToken, user }
  } catch {
    clearStoredAuth()
    return null
  }
}

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState({
    accessToken: null,
    user: null,
    status: 'restoring',
  })

  useEffect(() => {
    const restoredAuth = getStoredAuth()
    setAuth({
      accessToken: restoredAuth?.accessToken ?? null,
      user: restoredAuth?.user ?? null,
      status: restoredAuth ? 'authenticated' : 'anonymous',
    })
  }, [])

  const value = useMemo(() => {
    const completeLogin = ({ access_token: accessToken, user }) => {
      if (!accessToken || !user) {
        throw new Error('The server returned an incomplete login response.')
      }
      localStorage.setItem(TOKEN_STORAGE_KEY, accessToken)
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user))
      setAuth({ accessToken, user, status: 'authenticated' })
      return user
    }

    return {
      accessToken: auth.accessToken,
      currentUser: auth.user,
      status: auth.status,
      isAuthenticated: auth.status === 'authenticated',
      isRestoring: auth.status === 'restoring',
      login: async (credentials) => completeLogin(await api.post('/auth/login', credentials)),
      register: (registration) => api.post('/auth/register', registration),
      logout: () => {
        clearStoredAuth()
        setAuth({ accessToken: null, user: null, status: 'anonymous' })
      },
    }
  }, [auth])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
