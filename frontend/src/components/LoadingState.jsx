export function LoadingState({ label = 'Loading notes' }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
    >
      <span className="sr-only">{label}</span>
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="card-chai h-48 animate-pulse p-4"
          aria-hidden="true"
        >
          <div className="flex gap-1.5">
            <span className="h-5 w-16 rounded bg-muted" />
            <span className="h-5 w-14 rounded bg-muted" />
          </div>
          <div className="mt-4 h-4 w-3/4 rounded bg-muted" />
          <div className="mt-3 h-3 w-full rounded bg-muted" />
          <div className="mt-2 h-3 w-2/3 rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}
