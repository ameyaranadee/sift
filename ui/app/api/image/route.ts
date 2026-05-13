import { NextRequest, NextResponse } from 'next/server'

export async function GET(req: NextRequest) {
  const url = req.nextUrl.searchParams.get('url')
  if (!url) return new NextResponse('missing url', { status: 400 })

  let parsed: URL
  try {
    parsed = new URL(url)
  } catch {
    return new NextResponse('invalid url', { status: 400 })
  }

  if (!parsed.hostname.endsWith('.harvard.edu')) {
    return new NextResponse('disallowed host', { status: 403 })
  }

  const upstream = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
      'Referer': 'https://harvardartmuseums.org/',
    },
  })
  if (!upstream.ok) return new NextResponse('upstream error', { status: upstream.status })

  const contentType = upstream.headers.get('content-type') ?? 'image/jpeg'
  return new NextResponse(upstream.body, {
    headers: {
      'Content-Type': contentType,
      'Cache-Control': 'public, max-age=604800, immutable',
    },
  })
}
