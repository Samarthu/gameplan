<template>
  <node-view-wrapper class="file-attachment my-4 block" contenteditable="false">
    <!-- Inline PDF -->
    <figure
      v-if="variant === 'pdf'"
      class="group overflow-hidden rounded-xl border border-outline-gray-modals bg-surface-white shadow-sm"
    >
      <header
        class="flex items-center gap-3 border-b border-outline-gray-modals bg-surface-gray-1 px-3 py-2"
      >
        <span class="flex h-8 w-8 flex-shrink-0 overflow-hidden rounded-md">
          <FileThumb :file="thumbFile" />
        </span>
        <div class="flex min-w-0 flex-1 flex-col">
          <span
            class="truncate text-sm font-medium text-ink-gray-9"
            :title="displayName"
          >
            {{ displayName }}
          </span>
          <span class="text-xs text-ink-gray-5">{{ fileMetaLine }}</span>
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <button
            type="button"
            class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-9"
            title="Open fullscreen"
            @click="openPreview"
          >
            <MaximizeIcon class="h-4 w-4" />
          </button>
          <a
            :href="src"
            :download="displayName"
            class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-9"
            title="Download"
          >
            <DownloadIcon class="h-4 w-4" />
          </a>
        </div>
      </header>
      <div
        class="relative bg-surface-gray-1"
        :style="{ height: '520px' }"
      >
        <div
          v-if="!pdfLoaded"
          class="absolute inset-0 flex items-center justify-center gap-2 text-sm text-ink-gray-5"
        >
          <span
            class="h-4 w-4 animate-spin rounded-full border-2 border-outline-gray-3 border-t-ink-gray-8"
          />
          Loading PDF…
        </div>
        <iframe
          :src="pdfSrc"
          :title="displayName"
          class="absolute inset-0 h-full w-full"
          loading="lazy"
          @load="pdfLoaded = true"
        />
      </div>
    </figure>

    <!-- Inline image -->
    <figure
      v-else-if="variant === 'image'"
      class="overflow-hidden rounded-xl border border-outline-gray-modals bg-surface-gray-1"
    >
      <img
        :src="src"
        :alt="displayName"
        class="mx-auto block max-h-[70vh] w-auto max-w-full cursor-zoom-in object-contain"
        @click="openPreview"
        @error="imageFailed = true"
      />
      <figcaption
        class="flex items-center justify-between gap-3 border-t border-outline-gray-modals bg-surface-white px-3 py-2 text-xs text-ink-gray-6"
      >
        <span class="truncate font-medium text-ink-gray-8" :title="displayName">
          {{ displayName }}
        </span>
        <span class="shrink-0">{{ fileMetaLine }}</span>
      </figcaption>
    </figure>

    <!-- Inline video -->
    <figure
      v-else-if="variant === 'video'"
      class="overflow-hidden rounded-xl border border-outline-gray-modals bg-black"
    >
      <video
        :src="src"
        controls
        preload="metadata"
        class="block max-h-[70vh] w-full bg-black"
      />
      <figcaption
        class="flex items-center justify-between gap-3 border-t border-outline-gray-modals bg-surface-white px-3 py-2 text-xs text-ink-gray-6"
      >
        <span class="truncate font-medium text-ink-gray-8" :title="displayName">
          {{ displayName }}
        </span>
        <span class="shrink-0">{{ fileMetaLine }}</span>
      </figcaption>
    </figure>

    <!-- Inline audio -->
    <figure
      v-else-if="variant === 'audio'"
      class="flex items-center gap-3 rounded-xl border border-outline-gray-modals bg-surface-white p-3 shadow-sm"
    >
      <span class="flex h-12 w-12 flex-shrink-0 overflow-hidden rounded-lg">
        <FileThumb :file="thumbFile" />
      </span>
      <div class="flex min-w-0 flex-1 flex-col gap-1.5">
        <span
          class="truncate text-sm font-medium text-ink-gray-9"
          :title="displayName"
        >
          {{ displayName }}
        </span>
        <audio :src="src" controls preload="metadata" class="h-8 w-full" />
      </div>
    </figure>

    <!-- Everything else: rich smart chip -->
    <div
      v-else
      class="group flex items-center gap-3 rounded-xl border border-outline-gray-modals bg-surface-white p-3 shadow-sm transition-all hover:-translate-y-px hover:shadow-md"
    >
      <span class="flex h-12 w-12 flex-shrink-0 overflow-hidden rounded-lg">
        <FileThumb :file="thumbFile" />
      </span>
      <div class="flex min-w-0 flex-1 flex-col">
        <span
          class="truncate text-sm font-semibold text-ink-gray-9"
          :title="displayName"
        >
          {{ displayName }}
        </span>
        <span class="mt-0.5 text-xs text-ink-gray-5">
          {{ fileMetaLine }}
        </span>
      </div>
      <div class="flex shrink-0 items-center gap-1">
        <button
          v-if="src"
          type="button"
          class="inline-flex h-8 items-center gap-1 rounded-md bg-surface-gray-2 px-2.5 text-xs font-medium text-ink-gray-8 transition-colors hover:bg-surface-gray-3"
          @click="openPreview"
        >
          <EyeIcon class="h-3.5 w-3.5" />
          View
        </button>
        <a
          v-if="src"
          :href="src"
          :download="displayName"
          class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-9"
          title="Download"
          aria-label="Download"
        >
          <DownloadIcon class="h-4 w-4" />
        </a>
      </div>
    </div>

    <FilePreviewDialog v-model="previewOpen" :file="previewFile" />
  </node-view-wrapper>
</template>

<script>
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { h } from 'vue'
import FileThumb from '../AttachmentsPanel/FileThumb.vue'
import FilePreviewDialog from '../AttachmentsPanel/FilePreviewDialog.vue'

function safeString(v) {
  if (v === null || v === undefined) return ''
  if (typeof v === 'string') return v
  if (typeof v === 'number') return String(v)
  return ''
}

function safeNumber(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function formatBytes(bytes) {
  const n = safeNumber(bytes)
  if (!n || n < 1) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(n) / Math.log(1024))
  const size = n / Math.pow(1024, i)
  return `${size.toFixed(size >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}

function iconComponent(children) {
  return {
    render() {
      return h(
        'svg',
        {
          xmlns: 'http://www.w3.org/2000/svg',
          viewBox: '0 0 24 24',
          fill: 'none',
          stroke: 'currentColor',
          'stroke-width': 2,
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
        },
        children.map((c) => h(c.tag, c.attrs)),
      )
    },
  }
}

const DownloadIcon = iconComponent([
  { tag: 'path', attrs: { d: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' } },
  { tag: 'polyline', attrs: { points: '7 10 12 15 17 10' } },
  { tag: 'line', attrs: { x1: 12, y1: 15, x2: 12, y2: 3 } },
])
const EyeIcon = iconComponent([
  { tag: 'path', attrs: { d: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' } },
  { tag: 'circle', attrs: { cx: 12, cy: 12, r: 3 } },
])
const MaximizeIcon = iconComponent([
  { tag: 'polyline', attrs: { points: '15 3 21 3 21 9' } },
  { tag: 'polyline', attrs: { points: '9 21 3 21 3 15' } },
  { tag: 'line', attrs: { x1: 21, y1: 3, x2: 14, y2: 10 } },
  { tag: 'line', attrs: { x1: 3, y1: 21, x2: 10, y2: 14 } },
])

const IMAGE_EXT = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'avif'])
const VIDEO_EXT = new Set(['mp4', 'webm', 'mov', 'm4v'])
const AUDIO_EXT = new Set(['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a'])

export default {
  name: 'FileAttachmentView',
  components: {
    NodeViewWrapper,
    FileThumb,
    FilePreviewDialog,
    DownloadIcon,
    EyeIcon,
    MaximizeIcon,
  },
  props: nodeViewProps,
  data() {
    return {
      pdfLoaded: false,
      imageFailed: false,
      previewOpen: false,
    }
  },
  computed: {
    src() {
      return safeString(this.node.attrs.src)
    },
    fileName() {
      return safeString(this.node.attrs.fileName)
    },
    mimeType() {
      return safeString(this.node.attrs.mimeType).toLowerCase()
    },
    fileSize() {
      return safeNumber(this.node.attrs.fileSize)
    },
    displayName() {
      if (this.fileName) return this.fileName
      if (!this.src) return 'Attachment'
      try {
        const url = new URL(this.src, window.location.origin)
        const parts = url.pathname.split('/').filter(Boolean)
        return decodeURIComponent(parts[parts.length - 1] || 'Attachment')
      } catch (e) {
        return 'Attachment'
      }
    },
    ext() {
      const n = this.displayName
      if (!n.includes('.')) return ''
      return n.split('.').pop().toLowerCase()
    },
    variant() {
      const e = this.ext
      const m = this.mimeType
      if (!this.imageFailed && (IMAGE_EXT.has(e) || m.startsWith('image/')))
        return 'image'
      if (e === 'pdf' || m === 'application/pdf') return 'pdf'
      if (VIDEO_EXT.has(e) || m.startsWith('video/')) return 'video'
      if (AUDIO_EXT.has(e) || m.startsWith('audio/')) return 'audio'
      return 'other'
    },
    fileMetaLine() {
      const size = formatBytes(this.fileSize)
      const parts = [this.ext.toUpperCase(), size].filter(Boolean)
      return parts.join(' · ') || 'Click to open'
    },
    thumbFile() {
      return {
        file_name: this.displayName,
        file_url: this.src,
        file_type: this.mimeType,
      }
    },
    pdfSrc() {
      if (!this.src) return ''
      const sep = this.src.includes('#') ? '&' : '#'
      return `${this.src}${sep}toolbar=0&navpanes=0`
    },
    previewFile() {
      return {
        file_name: this.displayName,
        file_url: this.src,
        file_type: this.mimeType,
        file_size: this.fileSize,
      }
    },
  },
  methods: {
    openPreview() {
      if (!this.src) return
      this.previewOpen = true
    },
  },
}
</script>
