import { useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { FileUp, Upload } from 'lucide-react'

import { ApiError } from '../api/client.js'
import { createNote } from '../api/notes.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { Button } from '../components/Button.jsx'
import { LoadingState } from '../components/LoadingState.jsx'
import { formatFileSize } from '../lib/format.js'

const MAX_FILE_SIZE = 10 * 1024 * 1024
const YEARS = [1, 2, 3, 4]
const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]

const FIELD =
  'h-10 w-full rounded-md border border-card-edge bg-card-fill px-3 text-sm text-foreground transition-colors duration-200 outline-none placeholder:text-muted-foreground focus:border-card-edge-hover'

const SELECT =
  'h-10 w-full rounded-md border border-card-edge bg-popover px-3 text-sm text-popover-foreground transition-colors duration-200 outline-none focus:border-card-edge-hover'

const LABEL = 'text-sm font-medium text-foreground'

function validate(values) {
  const errors = {}
  if (!values.title.trim()) errors.title = 'Title is required.'
  if (!values.subject.trim()) errors.subject = 'Subject is required.'
  if (values.description.length > 2000) {
    errors.description = 'Description must be 2000 characters or fewer.'
  }
  if (!YEARS.includes(Number(values.academicYear))) {
    errors.academicYear = 'Choose an academic year.'
  }
  if (!SEMESTERS.includes(Number(values.semester))) {
    errors.semester = 'Choose a semester.'
  }
  if (!values.file) {
    errors.file = 'A PDF file is required.'
  } else if (!/\.pdf$/i.test(values.file.name)) {
    errors.file = 'Only PDF files are allowed.'
  } else if (values.file.size > MAX_FILE_SIZE) {
    errors.file = `File must be ${formatFileSize(MAX_FILE_SIZE)} or smaller.`
  }
  return errors
}

export default function UploadNote() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const { status } = useAuth()

  const [values, setValues] = useState({
    title: '',
    description: '',
    subject: '',
    topic: '',
    academicYear: '',
    semester: '',
    file: null,
  })
  const [errors, setErrors] = useState({})
  const [submitError, setSubmitError] = useState('')
  const [dragging, setDragging] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  function setField(name, value) {
    setValues((previous) => ({ ...previous, [name]: value }))
    setErrors((previous) => ({ ...previous, [name]: undefined }))
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragging(false)
    const [file] = event.dataTransfer.files
    if (file) setField('file', file)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const nextErrors = validate(values)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    setSubmitting(true)
    setSubmitError('')

    const formData = new FormData()
    formData.append('title', values.title.trim())
    formData.append('subject', values.subject.trim())
    formData.append('academic_year', values.academicYear)
    formData.append('semester', values.semester)
    if (values.description.trim()) {
      formData.append('description', values.description.trim())
    }
    if (values.topic.trim()) formData.append('topic', values.topic.trim())
    formData.append('file', values.file)

    try {
      const created = await createNote(formData)
      navigate(`/notes/${created.id}`)
    } catch (error) {
      // Session expired or missing: send the user to log in first.
      if (error instanceof ApiError && error.status === 401) {
        navigate('/login', { state: { from: '/upload' } })
        return
      }
      setSubmitError(error.message)
      setSubmitting(false)
    }
  }

  if (status === 'loading') {
    return <LoadingState label="Checking session" />
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" state={{ from: '/upload' }} replace />
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <header className="text-center">
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">
          Share your <span className="highlight">notes</span>
        </h1>
        <p className="mt-3 text-sm text-muted-foreground">
          Upload a PDF so other students can find and download it.
        </p>
      </header>

      <form
        onSubmit={handleSubmit}
        noValidate
        className="card-chai flex flex-col gap-5 p-6"
      >
        <div className="flex flex-col gap-1.5">
          <label className={LABEL} htmlFor="title">
            Title
          </label>
          <input
            id="title"
            className={FIELD}
            value={values.title}
            onChange={(event) => setField('title', event.target.value)}
            placeholder="e.g. Operating Systems unit 3"
          />
          {errors.title ? (
            <p className="text-xs text-muted-foreground">{errors.title}</p>
          ) : null}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className={LABEL} htmlFor="description">
            Description
          </label>
          <textarea
            id="description"
            rows={4}
            className="w-full rounded-md border border-card-edge bg-card-fill px-3 py-2 text-sm text-foreground transition-colors duration-200 outline-none placeholder:text-muted-foreground focus:border-card-edge-hover"
            value={values.description}
            onChange={(event) => setField('description', event.target.value)}
            placeholder="A short summary of what these notes cover"
          />
          {errors.description ? (
            <p className="text-xs text-muted-foreground">{errors.description}</p>
          ) : null}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <label className={LABEL} htmlFor="subject">
              Subject
            </label>
            <input
              id="subject"
              className={FIELD}
              value={values.subject}
              onChange={(event) => setField('subject', event.target.value)}
              placeholder="e.g. Computer Science"
            />
            {errors.subject ? (
              <p className="text-xs text-muted-foreground">{errors.subject}</p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={LABEL} htmlFor="topic">
              Topic (optional)
            </label>
            <input
              id="topic"
              className={FIELD}
              value={values.topic}
              onChange={(event) => setField('topic', event.target.value)}
              placeholder="e.g. Scheduling"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={LABEL} htmlFor="academic_year">
              Academic year
            </label>
            <select
              id="academic_year"
              className={SELECT}
              value={values.academicYear}
              onChange={(event) => setField('academicYear', event.target.value)}
            >
              <option value="">Select year</option>
              {YEARS.map((year) => (
                <option key={year} value={year}>
                  Year {year}
                </option>
              ))}
            </select>
            {errors.academicYear ? (
              <p className="text-xs text-muted-foreground">
                {errors.academicYear}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <label className={LABEL} htmlFor="semester">
              Semester
            </label>
            <select
              id="semester"
              className={SELECT}
              value={values.semester}
              onChange={(event) => setField('semester', event.target.value)}
            >
              <option value="">Select semester</option>
              {SEMESTERS.map((semester) => (
                <option key={semester} value={semester}>
                  Semester {semester}
                </option>
              ))}
            </select>
            {errors.semester ? (
              <p className="text-xs text-muted-foreground">{errors.semester}</p>
            ) : null}
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className={LABEL}>PDF file</span>
          <div
            onDragOver={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            className={`flex flex-col items-center gap-2 rounded-md border border-dashed px-4 py-8 text-center transition-colors duration-200 ${
              dragging
                ? 'border-card-edge-hover bg-card-fill'
                : 'border-card-edge'
            }`}
          >
            <FileUp className="size-6 text-muted-foreground" aria-hidden="true" />
            {values.file ? (
              <p className="text-sm text-foreground">
                {values.file.name} · {formatFileSize(values.file.size)}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Drag a PDF here, or choose a file
              </p>
            )}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn-asym-mirror inline-flex h-9 items-center border border-card-edge px-3 text-sm font-medium text-foreground transition-colors duration-200 hover:border-card-edge-hover hover:bg-card-fill"
            >
              Choose file
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(event) => setField('file', event.target.files?.[0] ?? null)}
            />
            <p className="text-xs text-muted-foreground">
              PDF only, up to {formatFileSize(MAX_FILE_SIZE)}
            </p>
          </div>
          {errors.file ? (
            <p className="text-xs text-muted-foreground">{errors.file}</p>
          ) : null}
        </div>

        {submitError ? (
          <p role="alert" className="text-sm text-muted-foreground">
            {submitError}
          </p>
        ) : null}

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={submitting} iconRight={false}>
            <Upload className="size-4" aria-hidden="true" />
            {submitting ? 'Uploading' : 'Publish note'}
          </Button>
          <Button variant="ghost" to="/">
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
