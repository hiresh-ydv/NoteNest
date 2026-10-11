import { API_BASE_URL, requestJson } from './client.js'

const DEFAULT_PAGE_SIZE = 12

export async function listNotes({
  query,
  subject,
  academicYear,
  semester,
  sort,
  page,
  pageSize = DEFAULT_PAGE_SIZE,
} = {}) {
  const params = new URLSearchParams()
  if (query) params.set('query', query)
  if (subject) params.set('subject', subject)
  if (academicYear) params.set('academic_year', academicYear)
  if (semester) params.set('semester', semester)
  if (sort) params.set('sort', sort)
  if (page) params.set('page', page)
  params.set('page_size', pageSize)

  return requestJson(`/notes?${params.toString()}`)
}

export async function getNote(noteId) {
  return requestJson(`/notes/${noteId}`)
}

export async function createNote(formData) {
  return requestJson('/notes', { method: 'POST', body: formData })
}

export function downloadUrl(noteId) {
  return `${API_BASE_URL}/notes/${noteId}/download`
}
