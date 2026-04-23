<template>
  <img
    v-if="variant === 'image' && src"
    :src="src"
    :alt="name"
    class="h-full w-full object-cover"
    loading="lazy"
    @error="imageFailed = true"
  />
  <div
    v-else
    class="flex h-full w-full flex-col items-center justify-center gap-0.5"
    :class="tile.bg"
  >
    <component :is="tile.icon" class="h-4 w-4" :class="tile.icon_color" />
    <span
      class="text-[9px] font-semibold uppercase leading-none tracking-wide"
      :class="tile.text_color"
    >
      {{ tile.label }}
    </span>
  </div>
</template>

<script setup>
import { computed, h, ref } from 'vue'

const props = defineProps({
  file: { type: Object, required: true },
})

const imageFailed = ref(false)

const name = computed(() => safeString(props.file?.file_name))
const src = computed(() => safeString(props.file?.file_url))
const mime = computed(() => safeString(props.file?.file_type).toLowerCase())
const ext = computed(() => {
  const n = name.value
  if (!n || !n.includes('.')) return ''
  return n.split('.').pop().toLowerCase()
})

function safeString(v) {
  if (v === null || v === undefined) return ''
  if (typeof v === 'string') return v
  if (typeof v === 'number') return String(v)
  return ''
}

const IMAGE_EXT = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'avif'])
const PDF_EXT = new Set(['pdf'])
const DOC_EXT = new Set(['doc', 'docx', 'rtf', 'odt', 'pages'])
const SHEET_EXT = new Set(['xls', 'xlsx', 'csv', 'tsv', 'ods', 'numbers'])
const SLIDES_EXT = new Set(['ppt', 'pptx', 'odp', 'key'])
const VIDEO_EXT = new Set(['mp4', 'webm', 'mov', 'avi', 'mkv', 'm4v'])
const AUDIO_EXT = new Set(['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a'])
const ARCHIVE_EXT = new Set(['zip', 'tar', 'gz', 'rar', '7z', 'bz2'])
const CODE_EXT = new Set([
  'js', 'ts', 'jsx', 'tsx', 'py', 'rb', 'go', 'rs', 'java', 'kt',
  'php', 'c', 'cpp', 'h', 'cs', 'swift', 'sh', 'bash', 'json',
  'yaml', 'yml', 'toml', 'xml', 'html', 'css', 'scss', 'vue',
])
const TEXT_EXT = new Set(['txt', 'md', 'log'])

const variant = computed(() => {
  const e = ext.value
  const m = mime.value
  if (!imageFailed.value && (IMAGE_EXT.has(e) || m.startsWith('image/'))) return 'image'
  if (PDF_EXT.has(e) || m === 'application/pdf') return 'pdf'
  if (DOC_EXT.has(e) || m.includes('wordprocessingml') || m === 'application/msword') return 'doc'
  if (SHEET_EXT.has(e) || m.includes('spreadsheetml') || m === 'application/vnd.ms-excel') return 'sheet'
  if (SLIDES_EXT.has(e) || m.includes('presentationml')) return 'slides'
  if (VIDEO_EXT.has(e) || m.startsWith('video/')) return 'video'
  if (AUDIO_EXT.has(e) || m.startsWith('audio/')) return 'audio'
  if (ARCHIVE_EXT.has(e)) return 'archive'
  if (CODE_EXT.has(e)) return 'code'
  if (TEXT_EXT.has(e) || m.startsWith('text/')) return 'text'
  return 'generic'
})

// Minimal inline icons so we don't add deps
const FileIcon = {
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [
        h('path', { d: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' }),
        h('polyline', { points: '14 2 14 8 20 8' }),
      ],
    )
  },
}
const PdfIcon = FileIcon
const DocIcon = FileIcon
const SheetIcon = {
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [
        h('rect', { x: 3, y: 3, width: 18, height: 18, rx: 2 }),
        h('line', { x1: 3, y1: 9, x2: 21, y2: 9 }),
        h('line', { x1: 9, y1: 3, x2: 9, y2: 21 }),
      ],
    )
  },
}
const SlidesIcon = {
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [
        h('rect', { x: 2, y: 3, width: 20, height: 14, rx: 2 }),
        h('line', { x1: 8, y1: 21, x2: 16, y2: 21 }),
        h('line', { x1: 12, y1: 17, x2: 12, y2: 21 }),
      ],
    )
  },
}
const VideoIcon = {
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [
        h('polygon', { points: '23 7 16 12 23 17 23 7' }),
        h('rect', { x: 1, y: 5, width: 15, height: 14, rx: 2 }),
      ],
    )
  },
}
const AudioIcon = {
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [
        h('path', { d: 'M9 18V5l12-2v13' }),
        h('circle', { cx: 6, cy: 18, r: 3 }),
        h('circle', { cx: 18, cy: 16, r: 3 }),
      ],
    )
  },
}
const ArchiveIcon = {
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [
        h('rect', { x: 3, y: 3, width: 18, height: 4, rx: 1 }),
        h('path', { d: 'M5 7v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7' }),
        h('line', { x1: 10, y1: 12, x2: 14, y2: 12 }),
      ],
    )
  },
}
const CodeIcon = {
  render() {
    return h(
      'svg',
      {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        'stroke-width': 2,
        'stroke-linecap': 'round',
        'stroke-linejoin': 'round',
      },
      [h('polyline', { points: '16 18 22 12 16 6' }), h('polyline', { points: '8 6 2 12 8 18' })],
    )
  },
}

const TILE_MAP = {
  pdf:    { label: 'PDF',  icon: PdfIcon,    bg: 'bg-red-50',    text_color: 'text-red-700',    icon_color: 'text-red-600' },
  doc:    { label: 'DOC',  icon: DocIcon,    bg: 'bg-blue-50',   text_color: 'text-blue-700',   icon_color: 'text-blue-600' },
  sheet:  { label: 'XLS',  icon: SheetIcon,  bg: 'bg-green-50',  text_color: 'text-green-700',  icon_color: 'text-green-600' },
  slides: { label: 'PPT',  icon: SlidesIcon, bg: 'bg-orange-50', text_color: 'text-orange-700', icon_color: 'text-orange-600' },
  video:  { label: 'VIDEO',icon: VideoIcon,  bg: 'bg-purple-50', text_color: 'text-purple-700', icon_color: 'text-purple-600' },
  audio:  { label: 'AUDIO',icon: AudioIcon,  bg: 'bg-pink-50',   text_color: 'text-pink-700',   icon_color: 'text-pink-600' },
  archive:{ label: 'ZIP',  icon: ArchiveIcon,bg: 'bg-amber-50',  text_color: 'text-amber-700',  icon_color: 'text-amber-600' },
  code:   { label: 'CODE', icon: CodeIcon,   bg: 'bg-slate-100', text_color: 'text-slate-700',  icon_color: 'text-slate-600' },
  text:   { label: 'TXT',  icon: FileIcon,   bg: 'bg-gray-100',  text_color: 'text-gray-700',   icon_color: 'text-gray-600' },
}

const tile = computed(() => {
  if (variant.value in TILE_MAP) return TILE_MAP[variant.value]
  const fallbackLabel = (ext.value || 'FILE').toUpperCase().slice(0, 4)
  return {
    label: fallbackLabel,
    icon: FileIcon,
    bg: 'bg-gray-100',
    text_color: 'text-gray-700',
    icon_color: 'text-gray-600',
  }
})

defineExpose({ variant })
</script>
