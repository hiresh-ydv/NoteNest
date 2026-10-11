const FIELD =
  'h-10 rounded-md border border-card-edge bg-card-fill px-3 text-sm text-foreground transition-colors duration-200 outline-none placeholder:text-muted-foreground focus:border-card-edge-hover'

const SELECT =
  'h-10 rounded-md border border-card-edge bg-popover px-3 text-sm text-popover-foreground transition-colors duration-200 outline-none focus:border-card-edge-hover'

const YEARS = [1, 2, 3, 4]
const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]

export function FilterPanel({ filters, onChange, onClear }) {
  const hasFilters = Boolean(
    filters.subject || filters.academicYear || filters.semester,
  )

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <input
        type="text"
        aria-label="Filter by subject"
        placeholder="Subject"
        value={filters.subject}
        onChange={(event) => onChange({ subject: event.target.value })}
        className={`${FIELD} sm:max-w-48`}
      />
      <select
        aria-label="Filter by academic year"
        value={filters.academicYear}
        onChange={(event) => onChange({ academicYear: event.target.value })}
        className={`${SELECT} sm:max-w-36`}
      >
        <option value="">Any year</option>
        {YEARS.map((year) => (
          <option key={year} value={year}>
            Year {year}
          </option>
        ))}
      </select>
      <select
        aria-label="Filter by semester"
        value={filters.semester}
        onChange={(event) => onChange({ semester: event.target.value })}
        className={`${SELECT} sm:max-w-36`}
      >
        <option value="">Any semester</option>
        {SEMESTERS.map((semester) => (
          <option key={semester} value={semester}>
            Semester {semester}
          </option>
        ))}
      </select>
      <select
        aria-label="Sort notes"
        value={filters.sort}
        onChange={(event) => onChange({ sort: event.target.value })}
        className={`${SELECT} sm:ml-auto sm:max-w-44`}
      >
        <option value="newest">Newest first</option>
        <option value="downloads">Most downloaded</option>
      </select>
      {hasFilters ? (
        <button
          type="button"
          onClick={onClear}
          className="h-10 rounded-md px-3 text-sm font-medium text-muted-foreground transition-colors duration-200 hover:text-foreground"
        >
          Clear filters
        </button>
      ) : null}
    </div>
  )
}
