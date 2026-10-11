import { Outlet } from 'react-router-dom'

import { Backdrop } from '../components/Backdrop.jsx'
import { Navbar } from '../components/Navbar.jsx'
import { Footer } from '../components/Footer.jsx'

export function MainLayout() {
  return (
    <div className="relative isolate flex min-h-dvh flex-col overflow-x-clip">
      <Backdrop />
      <Navbar />
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8 sm:px-12 sm:py-12">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
