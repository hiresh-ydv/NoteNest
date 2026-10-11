import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext.jsx'
import { AuthForm } from '../components/AuthForm.jsx'
import { LoadingState } from '../components/LoadingState.jsx'

export default function Register() {
  const { status, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/'

  if (status === 'loading') return <LoadingState label="Checking session" />
  if (status === 'authenticated') return <Navigate to={from} replace />

  return (
    <AuthForm
      mode="register"
      onSubmit={async (email, password) => {
        await register(email, password)
        navigate(from, { replace: true })
      }}
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="text-brand hover:underline">
            Log in
          </Link>
        </>
      }
    />
  )
}
