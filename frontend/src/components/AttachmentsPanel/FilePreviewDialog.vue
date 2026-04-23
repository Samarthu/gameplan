<template>
  <Dialog
    v-model="isOpen"
    :options="{ title: displayName || 'Preview', size: '5xl' }"
  >
    <template #body-content>
      <div class="min-h-[40vh]">
        <template v-if="!file">
          <div
            class="flex h-[40vh] items-center justify-center text-sm text-ink-gray-5"
          >
            No file selected.
          </div>
        </template>

        <div
          v-else-if="previewVariant === 'image'"
          class="flex max-h-[80vh] items-center justify-center bg-surface-gray-1"
        >
          <img
            :src="file.file_url"
            :alt="displayName"
            class="max-h-[80vh] w-auto max-w-full object-contain"
          />
        </div>

        <iframe
          v-else-if="previewVariant === 'pdf'"
          :src="pdfSrc"
          :title="displayName"
          class="h-[80vh] w-full rounded-md bg-surface-gray-1"
        />

        <div
          v-else-if="previewVariant === 'video'"
          class="flex max-h-[80vh] items-center justify-center bg-black"
        >
          <video
            :src="file.file_url"
            controls
            class="max-h-[80vh] w-full"
          />
        </div>

        <div
          v-else-if="previewVariant === 'audio'"
          class="flex flex-col items-center gap-4 rounded-md bg-surface-gray-1 px-6 py-10"
        >
          <div class="h-16 w-16 overflow-hidden rounded-lg">
            <FileThumb :file="file" />
          </div>
          <p class="text-base font-medium text-ink-gray-9">
            {{ displayName }}
          </p>
          <audio :src="file.file_url" controls class="w-full max-w-xl" />
        </div>

        <div
          v-else
          class="flex flex-col items-center gap-4 rounded-md bg-surface-gray-1 px-6 py-12"
        >
          <div class="h-20 w-20 overflow-hidden rounded-lg">
            <FileThumb :file="file" />
          </div>
          <div class="text-center">
            <p class="text-base font-medium text-ink-gray-9">
              {{ displayName }}
            </p>
            <p class="mt-1 text-sm text-ink-gray-5">
              This file type can't be previewed here.
            </p>
          </div>
          <a
            :href="file.file_url"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1.5 rounded-md bg-ink-gray-9 px-3 py-1.5 text-sm font-medium text-white hover:bg-ink-gray-8"
          >
            Open in new tab
          </a>
        </div>

        <div
          v-if="file"
          class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-outline-gray-modals pt-4 text-sm"
        >
          <div class="flex min-w-0 flex-col">
            <span class="truncate font-medium text-ink-gray-9">
              {{ displayName }}
            </span>
            <span class="mt-0.5 text-xs text-ink-gray-5">
              {{ metaLine }}
            </span>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <a
              :href="file.file_url"
              :download="displayName"
              class="inline-flex items-center gap-1.5 rounded-md border border-outline-gray-modals bg-surface-white px-3 py-1.5 text-sm font-medium text-ink-gray-8 hover:bg-surface-gray-2"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="h-4 w-4"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Download
            </a>
            <a
              :href="file.file_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 rounded-md border border-outline-gray-modals bg-surface-white px-3 py-1.5 text-sm font-medium text-ink-gray-8 hover:bg-surface-gray-2"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="h-4 w-4"
              >
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
              Open
            </a>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import { Dialog } from 'frappe-ui'
import FileThumb from './FileThumb.vue'

dayjs.extend(relativeTime)

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  file: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

function safeString(v) {
  if (v === null || v === undefined) return ''
  return typeof v === 'string' ? v : typeof v === 'number' ? String(v) : ''
}

const displayName = computed(() => safeString(props.file?.file_name))

const fileType = computed(() => safeString(props.file?.file_type).toLowerCase())
const extension = computed(() => {
  const n = displayName.value
  if (!n.includes('.')) return ''
  return n.split('.').pop().toLowerCase()
})

const previewVariant = computed(() => {
  const e = extension.value
  const m = fileType.value
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'avif'].includes(e) || m.startsWith('image/')) {
    return 'image'
  }
  if (e === 'pdf' || m === 'application/pdf') return 'pdf'
  if (['mp4', 'webm', 'mov', 'm4v'].includes(e) || m.startsWith('video/')) return 'video'
  if (['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a'].includes(e) || m.startsWith('audio/')) return 'audio'
  return 'other'
})

const pdfSrc = computed(() => {
  if (!props.file?.file_url) return ''
  const sep = props.file.file_url.includes('#') ? '&' : '#'
  return `${props.file.file_url}${sep}toolbar=0&navpanes=0`
})

function formatBytes(bytes) {
  const n = Number(bytes)
  if (!Number.isFinite(n) || n < 1) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(n) / Math.log(1024))
  const size = n / Math.pow(1024, i)
  return `${size.toFixed(size >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}

const metaLine = computed(() => {
  if (!props.file) return ''
  const parts = []
  const size = formatBytes(props.file.file_size)
  if (size) parts.push(size)
  if (props.file.creation) {
    parts.push(`Uploaded ${dayjs(props.file.creation).fromNow()}`)
  }
  if (props.file.owner) parts.push(`by ${props.file.owner}`)
  return parts.join(' · ')
})
</script>
