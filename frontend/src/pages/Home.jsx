import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { listNotes } from '../api/notes.js'
import { Button } from '../components/Button.jsx'
import { SearchBar } from '../components/SearchBar.jsx'
import { FilterPanel } from '../components/FilterPanel.jsx'
import { NoteCard } from '../components/NoteCard.jsx'
import { Pagination } from '../components/Pagination.jsx'
import { LoadingState } from '../components/LoadingState.jsx'
import { EmptyState } from '../components/EmptyState.jsx'
import { ErrorState } from '../components/ErrorState.jsx'

const PAGE_SIZE = 12
const SORTS = new Set(['newest', 'downloads'])

// UI field name -> URL query parameter name.
const PARAM_KEYS = {
  academicYear: 'academic_year',
}

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams()

  const query = searchParams.get('query') ?? ''
  const subject = searchParams.get('subject') ?? ''
  const academicYear = searchParams.get('academic_year') ?? ''
  const semester = searchParams.get('semester') ?? ''
  const sortParam = searchParams.get('sort')
  const sort = SORTS.has(sortParam) ? sortParam : 'newest'
  const page = Math.max(
    1,
    Number.parseInt(searchParams.get('page') ?? '1', 10) || 1,
  )

  const [searchInput, setSearchInput] = useState(query)
  const [reloadKey, setReloadKey] = useState(0)
  const [state, setState] = useState({
    status: 'loading',
    data: null,
    error: null,
  })

  function updateParams(patch) {
    const next = new URLSearchParams(searchParams)
    for (const [key, value] of Object.entries(patch)) {
      const param = PARAM_KEYS[key] ?? key
      const isReset = value === '' || value == null
      const isFirstPage = param === 'page' && String(value) === '1'
      if (isReset || isFirstPage) next.delete(param)
      else next.set(param, String(value))
    }
    setSearchParams(next, { replace: true })
  }

  useEffect(() => {
    setSearchInput(query)
  }, [query])

  useEffect(() => {
    if (searchInput === query) return undefined
    const timer = setTimeout(() => {
      updateParams({ query: searchInput, page: 1 })
    }, 350)
    return () => clearTimeout(timer)
    // updateParams is intentionally read at fire time.
  }, [searchInput, query])

  useEffect(() => {
    let active = true
    setState((previous) => ({ ...previous, status: 'loading', error: null }))
    listNotes({
      query,
      subject,
      academicYear,
      semester,
      sort,
      page,
      pageSize: PAGE_SIZE,
    })
      .then((data) => {
        if (active) setState({ status: 'success', data, error: null })
      })
      .catch((error) => {
        if (active) setState({ status: 'error', data: null, error })
      })
    return () => {
      active = false
    }
  }, [query, subject, academicYear, semester, sort, page, reloadKey])

  const resultCount = state.data?.total ?? 0
  const totalPages = state.data?.total_pages ?? 1

  return (
    <div className="flex flex-col gap-8">
      <header className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Community library
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          Explore <span className="highlight">academic notes</span>
        </h1>
        <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">
          Browse notes shared by students across subjects, years and semesters.
          Search, filter and download the{' '}
          <span className="highlight">notes you need</span>.
        </p>
      </header>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="lg:flex-1">
            <SearchBar value={searchInput} onChange={setSearchInput} />
          </div>
          <Button to="/upload">Upload notes</Button>
        </div>
        <FilterPanel
          filters={{ subject, academicYear, semester, sort }}
          onChange={updateParams}
          onClear={() =>
            updateParams({
              subject: '',
              academicYear: '',
              semester: '',
              page: 1,
            })
          }
        />
      </section>

      {state.status === 'loading' ? <LoadingState /> : null}

      {state.status === 'error' ? (
        <ErrorState
          message={state.error?.message}
          onRetry={() => setReloadKey((key) => key + 1)}
        />
      ) : null}

      {state.status === 'success' && resultCount === 0 ? (
        <EmptyState
          title="No notes found"
          message="Try a different search, or upload the first note for this subject."
          actionLabel="Upload notes"
          actionTo="/upload"
        />
      ) : null}

      {state.status === 'success' && resultCount > 0 ? (
        <section className="flex flex-col gap-6">
          <p className="text-sm text-muted-foreground">
            Showing {state.data.items.length} of {resultCount} notes
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {state.data.items.map((note) => (
              <NoteCard key={note.id} note={note} />
            ))}
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            onPageChange={(nextPage) => {
              updateParams({ page: nextPage })
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
          />
        </section>
      ) : null}
    </div>
  )
}
