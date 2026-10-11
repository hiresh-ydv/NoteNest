import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  CalendarDays,
  Download,
  FileText,
  GraduationCap,
} from 'lucide-react'

import { downloadUrl, getNote } from '../api/notes.js'
import { Button } from '../components/Button.jsx'
import { ErrorState } from '../components/ErrorState.jsx'
import { LoadingState } from '../components/LoadingState.jsx'
import { formatDate, formatFileSize } from '../lib/format.js'

const CHIP =
  'rounded border border-card-edge px-2.5 py-1 text-xs text-muted-foreground'

function Meta({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  )
}

export default function NoteDetail() {
  const { noteId } = useParams()
  const [status, setStatus] = useState('loading')
  const [note, setNote] = useState(null)
  const [error, setError] = useState(null)
  const [downloads, setDownloads] = useState(0)

  const load = useCallback(() => {
    setStatus('loading')
    getNote(noteId)
      .then((data) => {
        setNote(data)
        setDownloads(data.download_count)
        setStatus('success')
      })
      .catch((err) => {
        setError(err)
        setStatus(err.status === 404 ? 'notfound' : 'error')
      })
  }, [noteId])

  useEffect(() => {
    load()
  }, [load])

  if (status === 'loading') {
    return (
      <div className="mx-auto max-w-3xl">
        <LoadingState label="Loading note" />
      </div>
    )
  }

  if (status === 'notfound') {
    return (
      <div className="mx-auto max-w-xl py-12 text-center">
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          404
        </p>
        <h1 className="mt-3 font-display text-2xl font-semibold text-foreground">
          Note not found
        </h1>
        <p className="mt-3 text-sm text-muted-foreground">
          This note may have been removed or the link is incorrect.
        </p>
        <Button to="/" className="mt-6">
          Back to explore
        </Button>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="mx-auto max-w-3xl">
        <ErrorState message={error?.message} onRetry={load} />
      </div>
    )
  }

  return (
    <article className="mx-auto flex max-w-3xl flex-col gap-6">
      <Link
        to="/"
        className="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground transition-colors duration-200 hover:text-brand"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Back to explore
      </Link>

      <header className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-1.5">
          <span className={CHIP}>Year {note.academic_year}</span>
          <span className={CHIP}>Semester {note.semester}</span>
          <span className={CHIP}>{note.subject}</span>
          {note.topic ? <span className={CHIP}>{note.topic}</span> : null}
        </div>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground">
          {note.title}
        </h1>
      </header>

      <div className="card-chai flex flex-col gap-5 p-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Meta
            icon={FileText}
            label="File"
            value={formatFileSize(note.file_size)}
          />
          <Meta
            icon={CalendarDays}
            label="Uploaded"
            value={formatDate(note.created_at)}
          />
          <Meta
            icon={GraduationCap}
            label="Subject"
            value={note.subject}
          />
          <Meta
            icon={Download}
            label="Downloads"
            value={downloads}
          />
        </div>

        <div className="border-t border-card-edge pt-5">
          <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Description
          </p>
          <p className="mt-2 text-sm leading-relaxed whitespace-pre-line text-foreground">
            {note.description || 'No description was provided for this note.'}
          </p>
        </div>

        <Button
          href={downloadUrl(note.id)}
          iconRight={false}
          onClick={() => setDownloads((count) => count + 1)}
          className="w-fit"
        >
          <Download className="size-4" aria-hidden="true" />
          Download PDF
        </Button>
      </div>
    </article>
  )
}
