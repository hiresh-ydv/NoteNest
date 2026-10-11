import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext.jsx'
import { AuthForm } from '../components/AuthForm.jsx'
import { LoadingState } from '../components/LoadingState.jsx'

export default function Login() {
  const { status, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/'

  if (status === 'loading') return <LoadingState label="Checking session" />
  if (status === 'authenticated') return <Navigate to={from} replace />

  return (
    <AuthForm
      mode="login"
      onSubmit={async (email, password) => {
        await login(email, password)
        navigate(from, { replace: true })
      }}
      footer={
        <>
          New to NoteNest?{' '}
          <Link to="/register" className="text-brand hover:underline">
            Create an account
          </Link>
        </>
      }
    />
  )
}
