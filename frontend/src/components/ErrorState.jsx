import { TriangleAlert } from 'lucide-react'

export function ErrorState({ message, onRetry }) {
  return (
    <div
      role="alert"
      className="card-chai flex flex-col items-center gap-3 px-6 py-16 text-center"
    >
      <TriangleAlert className="size-8 text-muted-foreground" aria-hidden="true" />
      <h2 className="font-display text-lg font-semibold text-foreground">
        Something went wrong
      </h2>
      <p className="max-w-sm text-sm text-muted-foreground">
        {message || 'The notes could not be loaded. Please try again.'}
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="btn-asym-mirror mt-2 inline-flex h-10 items-center border border-card-edge px-4 text-sm font-medium text-foreground transition-colors duration-200 hover:border-card-edge-hover hover:bg-card-fill"
        >
          Try again
        </button>
      ) : null}
    </div>
  )
}
