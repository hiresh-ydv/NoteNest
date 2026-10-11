import { Link } from 'react-router-dom'
import { ArrowUpRight, Download } from 'lucide-react'

import { formatFileSize } from '../lib/format.js'

const CHIP =
  'rounded border border-card-edge px-2 py-0.5 text-[11px] text-muted-foreground'

export function NoteCard({ note }) {
  return (
    <article className="card-chai flex flex-col p-4">
      <div className="flex flex-wrap gap-1.5">
        <span className={CHIP}>Year {note.academic_year}</span>
        <span className={CHIP}>Sem {note.semester}</span>
      </div>
      <h3 className="mt-3 font-display text-base leading-snug font-semibold text-foreground">
        {note.title}
      </h3>
      <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
        {note.description || note.topic || note.subject}
      </p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className={CHIP}>{note.subject}</span>
        {note.topic ? <span className={CHIP}>{note.topic}</span> : null}
      </div>
      <div className="mt-auto flex items-center justify-between gap-3 pt-4">
        <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Download className="size-3.5" aria-hidden="true" />
          {formatFileSize(note.file_size)} · {note.download_count} downloads
        </span>
        <Link
          to={`/notes/${note.id}`}
          className="btn-asym inline-flex h-8 items-center gap-1 bg-primary px-3 text-sm font-semibold text-primary-foreground transition-colors duration-200 hover:bg-primary/90"
        >
          View details
          <ArrowUpRight className="-ml-0.5 size-4" aria-hidden="true" />
        </Link>
      </div>
    </article>
  )
}
