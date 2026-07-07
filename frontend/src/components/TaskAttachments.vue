<template>
  <div class="flex h-full min-h-0 flex-col overflow-y-auto px-6 py-4">
    <FileUploader
      :upload-args="uploadArgs"
      @success="onUploadSuccess"
      ref="uploader"
    >
      <template v-slot="{ progress, uploading, openFileSelector, error, file }">
        <div
          class="relative flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-6 text-center transition-all"
          :class="
            dragActive
              ? 'border-ink-blue-3 bg-surface-blue-1 ring-2 ring-ink-blue-3/30'
              : 'border-outline-gray-modals bg-surface-gray-1 hover:border-outline-gray-3'
          "
          @dragenter.prevent="dragActive = true"
          @dragover.prevent="dragActive = true"
          @dragleave.prevent="dragActive = false"
          @drop.prevent="onDrop"
        >
          <p class="text-sm font-medium text-ink-gray-9">
            {{ uploading ? `Uploading ${file?.name || ''} (${progress}%)` : 'Drop files here' }}
          </p>
          <p v-if="!uploading" class="text-xs text-ink-gray-5">
            or
            <button class="font-medium text-ink-blue-3 hover:underline" @click="openFileSelector">
              browse from your device
            </button>
          </p>
          <div v-if="uploading" class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-3">
            <div
              class="h-full bg-ink-blue-3 transition-all duration-200"
              :style="{ width: progress + '%' }"
            />
          </div>
          <p v-if="error" class="text-xs text-ink-red-4">{{ error }}</p>
        </div>
      </template>
    </FileUploader>

    <div class="mt-4">
      <div
        v-if="!allFiles.length"
        class="rounded-xl border border-dashed border-outline-gray-modals px-6 py-8 text-center text-sm text-ink-gray-5"
      >
        No attachments yet. Files uploaded here or added in comments will show up.
      </div>
      <ul v-else class="flex flex-col gap-1.5">
        <li
          v-for="f in allFiles"
          :key="f.file_url"
          class="group flex items-center gap-3 rounded-xl border border-outline-gray-modals bg-surface-white p-2.5 hover:border-outline-gray-3 hover:shadow-sm"
        >
          <button
            type="button"
            class="block h-11 w-11 flex-shrink-0 overflow-hidden rounded-lg bg-surface-gray-2"
            @click="openPreview(f)"
          >
            <FileThumb :file="f" />
          </button>
          <div class="flex min-w-0 flex-1 flex-col">
            <button
              type="button"
              class="truncate text-left text-sm font-medium text-ink-gray-9 hover:text-ink-blue-3"
              :title="f.file_name"
              @click="openPreview(f)"
            >
              {{ f.file_name || 'Untitled file' }}
            </button>
            <span class="flex items-center gap-1.5 text-xs text-ink-gray-5">
              <span v-if="f.file_size">{{ formatBytes(f.file_size) }} ·</span>
              <span v-if="f.creation">{{ dayjs(f.creation).fromNow() }} ·</span>
              <span>{{ f.source === 'comment' ? 'From comment' : 'Uploaded' }}</span>
            </span>
          </div>
          <div
            class="flex shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
          >
            <a
              :href="f.file_url"
              :download="f.file_name"
              class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9"
              title="Download"
            >
              <LucideDownload class="h-4 w-4" />
            </a>
            <button
              v-if="f.source === 'upload'"
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 hover:bg-surface-red-1 hover:text-ink-red-4"
              title="Delete"
              @click="confirmDelete(f)"
            >
              <LucideTrash2 class="h-4 w-4" />
            </button>
          </div>
        </li>
      </ul>
    </div>

    <FilePreviewDialog v-model="previewOpen" :file="previewFile" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { createListResource, createResource, FileUploader } from 'frappe-ui'
import FileThumb from './AttachmentsPanel/FileThumb.vue'
import FilePreviewDialog from './AttachmentsPanel/FilePreviewDialog.vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const props = defineProps({
  taskId: { type: [String, Number], required: true },
})

const dragActive = ref(false)
const uploader = ref(null)
const previewOpen = ref(false)
const previewFile = ref(null)

// Files uploaded directly against the task
const attachments = createListResource({
  doctype: 'File',
  fields: ['name', 'file_name', 'file_url', 'file_size', 'file_type', 'creation'],
  filters: {
    attached_to_doctype: 'GP Task',
    attached_to_name: String(props.taskId),
  },
  orderBy: 'creation desc',
  pageLength: 999,
  auto: true,
  cache: ['GP Task Attachments', String(props.taskId)],
})

// Comments on this task — file/image URLs embedded in their content also
// count as attachments (comment uploads aren't attached to the task doc).
const comments = createListResource({
  doctype: 'GP Comment',
  fields: ['name', 'content', 'creation'],
  filters: {
    reference_doctype: 'GP Task',
    reference_name: String(props.taskId),
  },
  orderBy: 'creation desc',
  pageLength: 999,
  auto: true,
})

watch(
  () => props.taskId,
  (id) => {
    attachments.update({
      filters: { attached_to_doctype: 'GP Task', attached_to_name: String(id) },
      cache: ['GP Task Attachments', String(id)],
    })
    attachments.reload()
    comments.update({
      filters: { reference_doctype: 'GP Task', reference_name: String(id) },
    })
    comments.reload()
  },
)

function fileName(url) {
  try {
    return decodeURIComponent(url.split('/').pop().split('?')[0])
  } catch {
    return url
  }
}

const commentFiles = computed(() => {
  const out = []
  for (const c of comments.data || []) {
    if (!c.content) continue
    const doc = new DOMParser().parseFromString(c.content, 'text/html')
    for (const el of doc.querySelectorAll('[src], a[href]')) {
      const url = el.getAttribute('src') || el.getAttribute('href')
      if (!url || !/^\/(private\/)?files\//.test(url)) continue
      out.push({
        file_url: url,
        file_name: el.getAttribute('filename') || fileName(url),
        file_size: Number(el.getAttribute('filesize')) || null,
        creation: c.creation,
        source: 'comment',
      })
    }
  }
  return out
})

const allFiles = computed(() => {
  const seen = new Set()
  const merged = []
  const uploaded = (attachments.data || []).map((f) => ({ ...f, source: 'upload' }))
  for (const f of [...uploaded, ...commentFiles.value]) {
    if (seen.has(f.file_url)) continue
    seen.add(f.file_url)
    merged.push(f)
  }
  return merged.sort((a, b) => new Date(b.creation) - new Date(a.creation))
})

const uploadArgs = computed(() => ({
  doctype: 'GP Task',
  docname: String(props.taskId),
  private: 1,
}))

const deleteFile = createResource({
  url: 'frappe.client.delete',
  makeParams(name) {
    return { doctype: 'File', name }
  },
  onSuccess() {
    attachments.reload()
  },
})

function onDrop(e) {
  dragActive.value = false
  const files = e.dataTransfer?.files
  if (!files?.length || !uploader.value) return
  uploader.value.onFileAdd({ target: { files: [files[0]] } })
}

function onUploadSuccess() {
  attachments.reload()
}

function confirmDelete(f) {
  if (!window.confirm(`Delete "${f.file_name}"? This cannot be undone.`)) return
  deleteFile.submit(f.name)
}

function openPreview(f) {
  previewFile.value = f
  previewOpen.value = true
}

function formatBytes(bytes) {
  const n = Number(bytes)
  if (!Number.isFinite(n) || n < 1) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(n) / Math.log(1024))
  const size = n / Math.pow(1024, i)
  return `${size.toFixed(size >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}
</script>
