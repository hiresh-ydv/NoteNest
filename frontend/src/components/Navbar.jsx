import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { LogOut, MailWarning } from 'lucide-react'

import { useAuth } from '../auth/AuthContext.jsx'
import { ThemeToggle } from './ThemeToggle.jsx'

function navLinkClass({ isActive }) {
  const base =
    'text-sm font-medium transition-colors duration-200 hover:text-brand'
  return isActive
    ? `${base} text-foreground`
    : `${base} text-muted-foreground`
}

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const { user, status, isVerified, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 0)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header
      className={`sticky top-0 z-50 transition-colors duration-300 ${
        scrolled ? 'bg-background/60 backdrop-blur-md' : 'bg-transparent'
      }`}
    >
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-5 sm:px-12">
        <Link
          to="/"
          className="font-brand text-xl font-medium tracking-tight text-foreground"
        >
          NoteNest
        </Link>
        <div className="flex items-center gap-3 sm:gap-5">
          <NavLink to="/" end className={navLinkClass}>
            Explore
          </NavLink>
          <NavLink to="/upload" className={navLinkClass}>
            Upload
          </NavLink>

          {status === 'authenticated' ? (
            <div className="flex items-center gap-3">
              {!isVerified ? (
                <NavLink
                  to="/verify-email"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors duration-200 hover:text-brand"
                >
                  <MailWarning className="size-4" aria-hidden="true" />
                  Verify email
                </NavLink>
              ) : null}
              <span className="hidden max-w-40 truncate text-sm text-muted-foreground sm:inline">
                {user?.email}
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors duration-200 hover:text-brand"
              >
                <LogOut className="size-4" aria-hidden="true" />
                Log out
              </button>
            </div>
          ) : status === 'anonymous' ? (
            <div className="flex items-center gap-3 sm:gap-5">
              <NavLink to="/login" className={navLinkClass}>
                Log in
              </NavLink>
              <NavLink to="/register" className={navLinkClass}>
                Sign up
              </NavLink>
            </div>
          ) : null}

          <ThemeToggle />
        </div>
      </nav>
    </header>
  )
}
