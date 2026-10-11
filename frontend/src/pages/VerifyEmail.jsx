import { useEffect, useRef, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { BadgeCheck, MailCheck } from 'lucide-react'

import { ApiError } from '../api/client.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { Button } from '../components/Button.jsx'
import { LoadingState } from '../components/LoadingState.jsx'

const CODE_LENGTH = 6
const RESEND_COOLDOWN = 60

const FIELD =
  'h-11 w-full rounded-md border border-card-edge bg-card-fill px-3 text-center font-mono text-lg tracking-[0.4em] text-foreground transition-colors duration-200 outline-none placeholder:tracking-normal placeholder:text-muted-foreground focus:border-card-edge-hover'

export default function VerifyEmail() {
  const { status, user, isVerified, verifyEmail, resendOtp } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/'

  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [cooldown, setCooldown] = useState(0)
  const timer = useRef(null)

  useEffect(() => {
    if (cooldown <= 0) return undefined
    timer.current = window.setInterval(() => {
      setCooldown((seconds) => (seconds <= 1 ? 0 : seconds - 1))
    }, 1000)
    return () => window.clearInterval(timer.current)
  }, [cooldown])

  if (status === 'loading') return <LoadingState label="Checking session" />
  if (status === 'anonymous') {
    return <Navigate to="/login" state={{ from: '/verify-email' }} replace />
  }
  if (isVerified) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-4 py-10 text-center">
        <BadgeCheck className="size-10 text-brand" aria-hidden="true" />
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">
          You&apos;re <span className="highlight">verified</span>
        </h1>
        <p className="text-sm text-muted-foreground">
          Your email is already confirmed. You can upload notes.
        </p>
        <Button to={from}>Continue</Button>
      </div>
    )
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    try {
      await verifyEmail(code.trim())
      navigate(from, { replace: true })
    } catch (submitError) {
      setError(submitError.message)
      setSubmitting(false)
    }
  }

  async function handleResend() {
    setError('')
    setNotice('')
    try {
      const result = await resendOtp()
      setNotice(result?.detail || 'A new verification code has been sent.')
      setCooldown(RESEND_COOLDOWN)
    } catch (resendError) {
      if (resendError instanceof ApiError && resendError.status === 429) {
        setCooldown(RESEND_COOLDOWN)
      }
      setError(resendError.message)
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col gap-6">
      <header className="text-center">
        <div className="mb-4 flex justify-center">
          <span className="flex size-12 items-center justify-center rounded-full border border-card-edge">
            <MailCheck className="size-5 text-brand" aria-hidden="true" />
          </span>
        </div>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">
          Verify your <span className="highlight">email</span>
        </h1>
        <p className="mt-3 text-sm text-muted-foreground">
          Enter the {CODE_LENGTH}-digit code we sent to{' '}
          <span className="text-foreground">{user?.email}</span>. It expires in
          10 minutes.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        noValidate
        className="card-chai flex flex-col gap-5 p-6"
      >
        <div className="flex flex-col gap-1.5">
          <label
            className="text-sm font-medium text-foreground"
            htmlFor="code"
          >
            Verification code
          </label>
          <input
            id="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={CODE_LENGTH}
            className={FIELD}
            value={code}
            onChange={(event) =>
              setCode(event.target.value.replace(/\D/g, '').slice(0, CODE_LENGTH))
            }
            placeholder="000000"
          />
        </div>

        {error ? (
          <p role="alert" className="text-sm text-muted-foreground">
            {error}
          </p>
        ) : null}
        {notice ? (
          <p className="text-sm text-muted-foreground">{notice}</p>
        ) : null}

        <Button type="submit" disabled={submitting} iconRight={false}>
          <BadgeCheck className="size-4" aria-hidden="true" />
          {submitting ? 'Verifying' : 'Verify email'}
        </Button>

        <div className="text-center text-sm text-muted-foreground">
          Didn&apos;t get a code?{' '}
          {cooldown > 0 ? (
            <span>Resend in {cooldown}s</span>
          ) : (
            <button
              type="button"
              onClick={handleResend}
              className="text-brand hover:underline"
            >
              Resend code
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
