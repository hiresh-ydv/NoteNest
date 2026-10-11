import { Search, X } from 'lucide-react'

export function SearchBar({ value, onChange }) {
  return (
    <div className="relative w-full">
      <Search
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden="true"
      />
      <input
        type="search"
        aria-label="Search notes"
        placeholder="Search by title, subject or topic"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-md border border-card-edge bg-card-fill pr-9 pl-9 text-sm text-foreground transition-colors duration-200 outline-none placeholder:text-muted-foreground focus:border-card-edge-hover"
      />
      {value ? (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => onChange('')}
          className="absolute top-1/2 right-2 flex size-6 -translate-y-1/2 items-center justify-center rounded text-muted-foreground transition-colors hover:text-foreground"
        >
          <X className="size-4" aria-hidden="true" />
        </button>
      ) : null}
    </div>
  )
}
