import { Routes, Route } from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext.jsx'
import { MainLayout } from './layouts/MainLayout.jsx'
import Home from './pages/Home.jsx'
import NoteDetail from './pages/NoteDetail.jsx'
import UploadNote from './pages/UploadNote.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import VerifyEmail from './pages/VerifyEmail.jsx'
import NotFound from './pages/NotFound.jsx'

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/notes/:noteId" element={<NoteDetail />} />
          <Route path="/upload" element={<UploadNote />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
