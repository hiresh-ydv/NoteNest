import { ChevronLeft, ChevronRight } from 'lucide-react'

const NAV_BUTTON =
  'inline-flex h-9 items-center gap-1 rounded-md border border-card-edge px-3 text-sm font-medium text-foreground transition-colors duration-200 hover:border-card-edge-hover disabled:cursor-not-allowed disabled:opacity-40'

export function Pagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) return null

  const pages = Array.from({ length: totalPages }, (_, index) => index + 1)

  return (
    <nav
      aria-label="Pagination"
      className="mt-10 flex items-center justify-center gap-2"
    >
      <button
        type="button"
        className={NAV_BUTTON}
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
      >
        <ChevronLeft className="size-4" aria-hidden="true" />
        Previous
      </button>
      <div className="flex items-center gap-1">
        {pages.map((number) => (
          <button
            key={number}
            type="button"
            aria-current={number === page ? 'page' : undefined}
            onClick={() => onPageChange(number)}
            className={`size-9 rounded-md text-sm font-medium transition-colors duration-200 ${
              number === page
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {number}
          </button>
        ))}
      </div>
      <button
        type="button"
        className={NAV_BUTTON}
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
      >
        Next
        <ChevronRight className="size-4" aria-hidden="true" />
      </button>
    </nav>
  )
}
