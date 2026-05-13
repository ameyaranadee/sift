import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getArtwork, type ArtworkDetail } from '@/lib/api'

const serif = 'var(--font-cormorant), Georgia, serif'
const sans = 'var(--font-inter), system-ui, sans-serif'

export default async function ArtworkPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: idStr } = await params
  const id = parseInt(idStr, 10)
  if (isNaN(id)) notFound()

  let artwork: ArtworkDetail
  try {
    artwork = await getArtwork(id)
  } catch {
    notFound()
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#FAF8F4', color: '#1C1917' }}>
      <style>{`
        .link-nav        { color: #1C1917; text-decoration: none; transition: color 0.15s; }
        .link-nav:hover  { color: #8B6F47; }
        .link-back       { color: #9C8575; text-decoration: none; transition: color 0.15s; }
        .link-back:hover { color: #1C1917; }
        .link-ext        { color: #8B6F47; transition: opacity 0.15s; }
        .link-ext:hover  { opacity: 0.7; }
      `}</style>

      {/* Header */}
      <header
        className="px-6 py-4 flex items-center justify-between"
        style={{ borderBottom: '1px solid #E5DDD3' }}
      >
        <Link
          href="/"
          className="link-nav"
          style={{ fontFamily: serif, fontStyle: 'italic', fontSize: '1.25rem' }}
        >
          Sift
        </Link>
        <span style={{ fontFamily: sans, fontSize: '0.75rem', color: '#9C8575' }}>
          Harvard Art Museums
        </span>
      </header>

      <div className="px-6 py-10 max-w-5xl mx-auto">
        <Link
          href="/"
          className="link-back inline-flex items-center gap-1 mb-10"
          style={{ fontFamily: sans, fontSize: '0.8125rem' }}
        >
          ← back
        </Link>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
          {/* Image */}
          {artwork.primary_image_url && (
            <div>
              <img
                src={artwork.primary_image_url}
                alt={artwork.title ?? ''}
                referrerPolicy="no-referrer"
                className="w-full h-auto"
                style={{ display: 'block' }}
              />
            </div>
          )}

          {/* Metadata */}
          <div>
            <h1 style={{ fontFamily: serif, fontSize: '2rem', lineHeight: 1.25, marginBottom: '8px', fontWeight: 400 }}>
              {artwork.title ?? 'Untitled'}
            </h1>

            {artwork.artist_name && (
              <p style={{ fontFamily: sans, fontSize: '0.9375rem', color: '#9C8575', marginBottom: '4px' }}>
                {artwork.artist_name}
                {artwork.artist_display_date ? ` (${artwork.artist_display_date})` : ''}
              </p>
            )}
            {artwork.dated && (
              <p style={{ fontFamily: sans, fontSize: '0.875rem', color: '#9C8575', marginBottom: '24px' }}>
                {artwork.dated}
              </p>
            )}

            <div style={{ borderTop: '1px solid #E5DDD3', paddingTop: '24px' }}>
              <MetaTable rows={[
                { label: 'Medium',         value: artwork.medium },
                { label: 'Technique',      value: artwork.technique },
                { label: 'Classification', value: artwork.classification },
                { label: 'Culture',        value: artwork.culture },
                { label: 'Department',     value: artwork.department },
                { label: 'Dimensions',     value: artwork.dimensions },
                { label: 'Period',         value: artwork.period },
                { label: 'Credit',         value: artwork.credit_line },
              ]} />
            </div>

            {(artwork.description || artwork.label_text) && (
              <div style={{ borderTop: '1px solid #E5DDD3', paddingTop: '24px', marginTop: '24px' }}>
                <p style={{ fontFamily: sans, fontSize: '0.875rem', color: '#1C1917', lineHeight: 1.7 }}>
                  {artwork.description ?? artwork.label_text}
                </p>
              </div>
            )}

            {artwork.artwork_url && (
              <div style={{ borderTop: '1px solid #E5DDD3', paddingTop: '24px', marginTop: '24px' }}>
                <a
                  href={artwork.artwork_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="link-ext"
                  style={{ fontFamily: sans, fontSize: '0.8125rem' }}
                >
                  View at Harvard Art Museums →
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function MetaTable({ rows }: { rows: { label: string; value: string | null | undefined }[] }) {
  const visible = rows.filter(r => r.value)
  if (!visible.length) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {visible.map(({ label, value }) => (
        <div key={label} style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
          <span
            style={{
              fontFamily: sans,
              fontSize: '0.6875rem',
              color: '#9C8575',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              width: '100px',
              flexShrink: 0,
              paddingTop: '2px',
            }}
          >
            {label}
          </span>
          <span style={{ fontFamily: sans, fontSize: '0.875rem', color: '#1C1917', lineHeight: 1.5 }}>
            {value}
          </span>
        </div>
      ))}
    </div>
  )
}
