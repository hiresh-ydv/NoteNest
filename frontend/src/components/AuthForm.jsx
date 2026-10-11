import { useState } from 'react'
import { Eye, EyeOff, LogIn, UserPlus } from 'lucide-react'

import { Button } from './Button.jsx'

const FIELD =
  'h-10 w-full rounded-md border border-card-edge bg-card-fill px-3 text-sm text-foreground transition-colors duration-200 outline-none placeholder:text-muted-foreground focus:border-card-edge-hover'

const LABEL = 'text-sm font-medium text-foreground'

export function AuthForm({ mode, onSubmit, footer }) {
  const isRegister = mode === 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const Icon = isRegister ? UserPlus : LogIn
  const submitLabel = isRegister ? 'Create account' : 'Log in'

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await onSubmit(email.trim(), password)
    } catch (submitError) {
      setError(submitError.message)
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col gap-6">
      <header className="text-center">
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">
          {isRegister ? (
            <>
              Create your <span className="highlight">account</span>
            </>
          ) : (
            <>
              Welcome <span className="highlight">back</span>
            </>
          )}
        </h1>
        <p className="mt-3 text-sm text-muted-foreground">
          {isRegister
            ? 'An account lets you upload notes. The library stays open to everyone.'
            : 'Log in to upload notes. Browsing and downloads are always open.'}
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        noValidate
        className="card-chai flex flex-col gap-5 p-6"
      >
        <div className="flex flex-col gap-1.5">
          <label className={LABEL} htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            className={FIELD}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className={LABEL} htmlFor="password">
            Password
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              required
              minLength={isRegister ? 8 : undefined}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              className={`${FIELD} pr-10`}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={isRegister ? 'At least 8 characters' : 'Your password'}
            />
            <button
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={showPassword}
              className="absolute top-1/2 right-2 flex size-7 -translate-y-1/2 items-center justify-center rounded text-muted-foreground transition-colors duration-200 hover:text-foreground"
            >
              {showPassword ? (
                <EyeOff className="size-4" aria-hidden="true" />
              ) : (
                <Eye className="size-4" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>

        {error ? (
          <p role="alert" className="text-sm text-muted-foreground">
            {error}
          </p>
        ) : null}

        <Button type="submit" disabled={submitting} iconRight={false}>
          <Icon className="size-4" aria-hidden="true" />
          {submitting ? 'Please wait' : submitLabel}
        </Button>

        {footer ? (
          <p className="text-center text-sm text-muted-foreground">{footer}</p>
        ) : null}
      </form>
    </div>
  )
}
