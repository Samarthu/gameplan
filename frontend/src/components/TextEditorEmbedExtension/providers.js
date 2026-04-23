const YOUTUBE_HOSTS = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be'])
const VIMEO_HOSTS = new Set(['vimeo.com', 'www.vimeo.com', 'player.vimeo.com'])
const LOOM_HOSTS = new Set(['loom.com', 'www.loom.com'])
const FIGMA_HOSTS = new Set(['figma.com', 'www.figma.com'])
const GDRIVE_HOSTS = new Set(['drive.google.com', 'docs.google.com'])

function parseUrl(raw) {
  if (typeof raw !== 'string') return null
  const trimmed = raw.trim()
  if (!trimmed) return null
  try {
    const url = new URL(trimmed)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
    return url
  } catch (e) {
    return null
  }
}

function toYouTubeEmbed(url) {
  if (url.hostname === 'youtu.be') {
    const id = url.pathname.replace(/^\//, '').split('/')[0]
    if (!id) return null
    return `https://www.youtube.com/embed/${encodeURIComponent(id)}`
  }
  if (url.pathname === '/watch') {
    const id = url.searchParams.get('v')
    if (!id) return null
    return `https://www.youtube.com/embed/${encodeURIComponent(id)}`
  }
  if (url.pathname.startsWith('/embed/')) {
    return `https://www.youtube.com${url.pathname}`
  }
  if (url.pathname.startsWith('/shorts/')) {
    const id = url.pathname.split('/')[2]
    if (!id) return null
    return `https://www.youtube.com/embed/${encodeURIComponent(id)}`
  }
  return null
}

function toVimeoEmbed(url) {
  if (url.hostname === 'player.vimeo.com') {
    return `https://player.vimeo.com${url.pathname}`
  }
  const id = url.pathname.split('/').filter(Boolean)[0]
  if (!id || !/^\d+$/.test(id)) return null
  return `https://player.vimeo.com/video/${id}`
}

function toLoomEmbed(url) {
  const match = url.pathname.match(/^\/(share|embed)\/([a-zA-Z0-9]+)/)
  if (!match) return null
  return `https://www.loom.com/embed/${encodeURIComponent(match[2])}`
}

function toFigmaEmbed(url) {
  if (url.pathname.startsWith('/embed')) {
    return `https://www.figma.com${url.pathname}${url.search || ''}`
  }
  const allowedPrefixes = ['/file/', '/proto/', '/design/', '/board/', '/slides/']
  if (!allowedPrefixes.some((p) => url.pathname.startsWith(p))) return null
  return `https://www.figma.com/embed?embed_host=gameplan&url=${encodeURIComponent(url.toString())}`
}

function toGoogleDriveEmbed(url) {
  if (url.hostname === 'drive.google.com') {
    const match = url.pathname.match(/\/file\/d\/([^/]+)/)
    if (match) return `https://drive.google.com/file/d/${match[1]}/preview`
    return null
  }
  if (url.hostname === 'docs.google.com') {
    if (
      url.pathname.startsWith('/document/') ||
      url.pathname.startsWith('/spreadsheets/') ||
      url.pathname.startsWith('/presentation/') ||
      url.pathname.startsWith('/forms/')
    ) {
      return url.toString().replace(/\/edit\b.*$/, '/preview').replace(/\/view\b.*$/, '/preview')
    }
  }
  return null
}

export function resolveEmbed(raw) {
  const url = parseUrl(raw)
  if (!url) return null
  const host = url.hostname.toLowerCase()

  if (YOUTUBE_HOSTS.has(host)) {
    const src = toYouTubeEmbed(url)
    if (src) return { provider: 'youtube', src, aspectRatio: '16 / 9' }
  }
  if (VIMEO_HOSTS.has(host)) {
    const src = toVimeoEmbed(url)
    if (src) return { provider: 'vimeo', src, aspectRatio: '16 / 9' }
  }
  if (LOOM_HOSTS.has(host)) {
    const src = toLoomEmbed(url)
    if (src) return { provider: 'loom', src, aspectRatio: '16 / 9' }
  }
  if (FIGMA_HOSTS.has(host)) {
    const src = toFigmaEmbed(url)
    if (src) return { provider: 'figma', src, aspectRatio: '4 / 3' }
  }
  if (GDRIVE_HOSTS.has(host)) {
    const src = toGoogleDriveEmbed(url)
    if (src) return { provider: 'google-drive', src, aspectRatio: '4 / 3' }
  }
  return null
}

export function isAllowedEmbedSrc(src) {
  const url = parseUrl(src)
  if (!url) return false
  const host = url.hostname.toLowerCase()
  return (
    host === 'www.youtube.com' ||
    host === 'youtube.com' ||
    host === 'player.vimeo.com' ||
    host === 'www.loom.com' ||
    host === 'www.figma.com' ||
    host === 'drive.google.com' ||
    host === 'docs.google.com'
  )
}

export const SUPPORTED_PROVIDERS = ['YouTube', 'Vimeo', 'Loom', 'Figma', 'Google Drive / Docs']
