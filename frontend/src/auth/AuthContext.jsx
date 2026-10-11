import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

import { ApiError } from '../api/client.js'
import {
  getMe,
  loginUser,
  logoutUser,
  registerUser,
  resendOtp as resendOtpRequest,
  verifyEmail as verifyEmailRequest,
} from '../api/auth.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // loading: restoring on first load | authenticated | anonymous
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    let active = true
    getMe()
      .then((data) => {
        if (!active) return
        setUser(data)
        setStatus('authenticated')
      })
      .catch((error) => {
        if (!active) return
        // 401 simply means "not signed in yet".
        if (error instanceof ApiError && error.status !== 401) {
          // Any other error: stay anonymous rather than blocking the app.
        }
        setUser(null)
        setStatus('anonymous')
      })
    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (email, password) => {
    const data = await loginUser(email, password)
    setUser(data)
    setStatus('authenticated')
    return data
  }, [])

  const register = useCallback(async (email, password) => {
    const data = await registerUser(email, password)
    setUser(data)
    setStatus('authenticated')
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await logoutUser()
    } finally {
      setUser(null)
      setStatus('anonymous')
    }
  }, [])

  const verifyEmail = useCallback(async (code) => {
    const data = await verifyEmailRequest(code)
    setUser(data)
    return data
  }, [])

  const resendOtp = useCallback(async () => {
    return resendOtpRequest()
  }, [])

  const value = useMemo(
    () => ({
      user,
      status,
      isVerified: Boolean(user?.email_verified),
      login,
      register,
      logout,
      verifyEmail,
      resendOtp,
    }),
    [user, status, login, register, logout, verifyEmail, resendOtp],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
