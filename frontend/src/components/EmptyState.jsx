import { FileSearch } from 'lucide-react'

import { Button } from './Button.jsx'

export function EmptyState({
  title = 'No notes found',
  message = 'Try a different search or clear the filters.',
  actionLabel,
  actionTo,
}) {
  return (
    <div className="card-chai flex flex-col items-center gap-3 px-6 py-16 text-center">
      <FileSearch className="size-8 text-muted-foreground" aria-hidden="true" />
      <h2 className="font-display text-lg font-semibold text-foreground">
        {title}
      </h2>
      <p className="max-w-sm text-sm text-muted-foreground">{message}</p>
      {actionLabel && actionTo ? (
        <Button to={actionTo} className="mt-2">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  )
}
