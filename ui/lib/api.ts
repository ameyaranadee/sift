const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export interface ArtworkResult {
  id: number
  title: string | null
  artist_name: string | null
  culture: string | null
  division: string | null
  dated: string | null
  century: string | null
  medium: string | null
  classification: string | null
  primary_image_url: string | null
  artwork_url: string | null
  similarity: number
}

export interface ArtworkDetail {
  id: number
  object_number: string | null
  title: string | null
  dated: string | null
  date_begin: number | null
  date_end: number | null
  century: string | null
  period: string | null
  medium: string | null
  technique: string | null
  classification: string | null
  culture: string | null
  division: string | null
  department: string | null
  artist_name: string | null
  artist_culture: string | null
  artist_display_date: string | null
  artist_birthplace: string | null
  artist_deathplace: string | null
  dimensions: string | null
  dim_height_cm: number | null
  dim_width_cm: number | null
  description: string | null
  label_text: string | null
  credit_line: string | null
  primary_image_url: string | null
  artwork_url: string | null
  source: string | null
}

export interface SearchResponse {
  results: ArtworkResult[]
  count: number
}

type Filters = {
  classification?: string
  century?: string
  culture?: string
  division?: string
}

export async function searchByText(q: string, limit = 20, filters: Filters = {}): Promise<SearchResponse> {
  const res = await fetch(`${API_URL}/search/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ q, limit, threshold: 0.3, ...filters }),
  })
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`)
  return res.json()
}

export async function searchByImage(file: File, limit = 20, filters: Filters = {}): Promise<SearchResponse> {
  const form = new FormData()
  form.append('image', file)
  const params = new URLSearchParams({ limit: String(limit), threshold: '0.3' })
  Object.entries(filters).forEach(([k, v]) => v && params.set(k, v))
  const res = await fetch(`${API_URL}/search/image?${params}`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`)
  return res.json()
}

export async function getRandomArtworks(limit = 20): Promise<SearchResponse> {
  const res = await fetch(`${API_URL}/artworks/random?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch random artworks')
  return res.json()
}

export async function getArtwork(id: number): Promise<ArtworkDetail> {
  const res = await fetch(`${API_URL}/artworks/${id}`, { cache: 'no-store' })
  if (!res.ok) throw new Error('Not found')
  return res.json()
}
