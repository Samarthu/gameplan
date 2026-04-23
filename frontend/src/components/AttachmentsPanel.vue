<template>
  <Teleport to="body">
    <div v-if="renderTree">
      <div
        class="fixed inset-0 z-40 bg-black/30 transition-opacity duration-200 ease-out"
        :class="
          visible
            ? 'opacity-100 pointer-events-auto'
            : 'opacity-0 pointer-events-none'
        "
        @click="close"
        aria-hidden="true"
      />
      <aside
        class="fixed inset-y-0 right-0 z-50 flex w-[min(100vw,28rem)] flex-col bg-surface-white shadow-2xl transition-transform duration-300 ease-out"
        :class="
          visible ? 'translate-x-0' : 'translate-x-full pointer-events-none'
        "
        role="dialog"
        aria-label="Attachments"
        :aria-hidden="!visible"
        @transitionend.self="onTransitionEnd"
      >
        <header
          class="flex items-center justify-between border-b border-outline-gray-modals px-5 py-4"
        >
          <div class="flex items-center gap-2.5">
            <span
              class="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-gray-2 text-ink-gray-8"
            >
              <PaperclipIcon class="h-4 w-4" />
            </span>
            <h2 class="text-base font-semibold text-ink-gray-9">Attachments</h2>
            <span
              v-if="fileCount > 0"
              class="rounded-full bg-surface-gray-2 px-2 py-0.5 text-xs font-medium text-ink-gray-7"
            >
              {{ fileCount }}
            </span>
          </div>
          <button
            class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-gray-2"
            @click="close"
            aria-label="Close attachments panel"
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
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </header>

        <div class="relative flex-1 overflow-y-auto px-5 py-5">
          <FileUploader
            :upload-args="uploadArgs"
            @success="onUploadSuccess"
            @failure="onUploadFailure"
            ref="uploader"
          >
            <template
              v-slot="{ progress, uploading, openFileSelector, error, file }"
            >
              <div
                class="relative flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 text-center transition-all"
                :class="
                  dragActive
                    ? 'border-ink-blue-3 bg-surface-blue-1 ring-2 ring-ink-blue-3/30'
                    : 'border-outline-gray-modals bg-gradient-to-b from-surface-gray-1 to-surface-white hover:border-outline-gray-3'
                "
                @dragenter.prevent="dragActive = true"
                @dragover.prevent="dragActive = true"
                @dragleave.prevent="dragActive = false"
                @drop.prevent="(e) => onDrop(e)"
              >
                <span
                  class="flex h-11 w-11 items-center justify-center rounded-full bg-surface-white text-ink-gray-7 shadow-sm ring-1 ring-outline-gray-modals"
                >
                  <UploadCloudIcon class="h-5 w-5" />
                </span>
                <div>
                  <p class="text-sm font-medium text-ink-gray-9">
                    {{
                      uploading
                        ? `Uploading ${file?.name || ''}`
                        : 'Drop files here'
                    }}
                  </p>
                  <p class="mt-0.5 text-xs text-ink-gray-5">
                    <template v-if="uploading">
                      {{ progress }}% uploaded
                    </template>
                    <template v-else>
                      or
                      <button
                        class="font-medium text-ink-blue-3 hover:underline"
                        @click="openFileSelector"
                      >
                        browse from your device
                      </button>
                    </template>
                  </p>
                </div>
                <div
                  v-if="uploading"
                  class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-3"
                >
                  <div
                    class="h-full bg-ink-blue-3 transition-all duration-200 ease-out"
                    :style="{ width: progress + '%' }"
                  />
                </div>
                <p v-if="error" class="mt-1 text-xs text-ink-red-4">
                  {{ error }}
                </p>
              </div>
            </template>
          </FileUploader>

          <div class="mt-5">
            <div
              v-if="attachments.loading && !attachments.data?.length"
              class="flex flex-col items-center gap-2 py-10 text-sm text-ink-gray-5"
            >
              <span
                class="h-5 w-5 animate-spin rounded-full border-2 border-outline-gray-3 border-t-ink-gray-8"
              />
              Loading attachments…
            </div>

            <div
              v-else-if="!attachments.data?.length"
              class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-outline-gray-modals bg-surface-gray-1/60 px-6 py-10 text-center"
            >
              <span
                class="flex h-12 w-12 items-center justify-center rounded-full bg-surface-white text-ink-gray-6 ring-1 ring-outline-gray-modals"
              >
                <PaperclipIcon class="h-5 w-5" />
              </span>
              <div>
                <p class="text-sm font-medium text-ink-gray-9">
                  No attachments yet
                </p>
                <p class="mt-0.5 text-xs text-ink-gray-5">
                  Drop a file above or click browse to start.
                </p>
              </div>
            </div>

            <template v-else>
              <div class="mb-2 flex items-center justify-between">
                <span
                  class="text-xs font-medium uppercase tracking-wide text-ink-gray-5"
                >
                  All files
                </span>
                <span class="text-xs text-ink-gray-5">
                  {{ totalSizeLabel }}
                </span>
              </div>
              <ul class="flex flex-col gap-1.5">
                <li
                  v-for="file in attachments.data"
                  :key="file.name"
                  class="group flex items-center gap-3 rounded-xl border border-outline-gray-modals bg-surface-white p-2.5 transition-all hover:-translate-y-px hover:border-outline-gray-3 hover:shadow-sm"
                >
                  <button
                    type="button"
                    class="block h-11 w-11 flex-shrink-0 overflow-hidden rounded-lg bg-surface-gray-2"
                    :title="`Preview ${file.file_name}`"
                    @click="openPreview(file)"
                  >
                    <FileThumb :file="file" />
                  </button>
                  <div class="flex min-w-0 flex-1 flex-col">
                    <button
                      type="button"
                      class="truncate text-left text-sm font-medium text-ink-gray-9 hover:text-ink-blue-3"
                      :title="file.file_name"
                      @click="openPreview(file)"
                    >
                      {{ file.file_name || 'Untitled file' }}
                    </button>
                    <span
                      class="flex items-center gap-1.5 text-xs text-ink-gray-5"
                    >
                      <span>{{ formatBytes(file.file_size) }}</span>
                      <span aria-hidden="true">·</span>
                      <span>{{ formatRelative(file.creation) }}</span>
                    </span>
                  </div>
                  <div
                    class="flex shrink-0 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
                  >
                    <button
                      type="button"
                      class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-9"
                      title="View"
                      aria-label="View file"
                      @click="openPreview(file)"
                    >
                      <EyeIcon class="h-4 w-4" />
                    </button>
                    <button
                      v-if="editor"
                      type="button"
                      class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-9"
                      title="Insert into document"
                      aria-label="Insert into document"
                      @click="insertIntoDoc(file)"
                    >
                      <PlusIcon class="h-4 w-4" />
                    </button>
                    <a
                      :href="file.file_url || '#'"
                      :download="file.file_name"
                      class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-gray-2 hover:text-ink-gray-9"
                      title="Download"
                      aria-label="Download file"
                    >
                      <DownloadIcon class="h-4 w-4" />
                    </a>
                    <button
                      type="button"
                      class="flex h-8 w-8 items-center justify-center rounded-md text-ink-gray-6 transition-colors hover:bg-surface-red-1 hover:text-ink-red-4 disabled:opacity-50"
                      :disabled="deleteInFlight === file.name"
                      title="Delete"
                      aria-label="Delete file"
                      @click="confirmDelete(file)"
                    >
                      <TrashIcon class="h-4 w-4" />
                    </button>
                  </div>
                </li>
              </ul>
            </template>
          </div>
        </div>

        <transition
          enter-active-class="transition-all duration-200"
          leave-active-class="transition-all duration-150"
          enter-from-class="opacity-0 translate-y-2"
          leave-to-class="opacity-0 translate-y-2"
        >
          <div
            v-if="toast.visible"
            class="pointer-events-none absolute bottom-5 left-1/2 z-10 -translate-x-1/2 rounded-full bg-ink-gray-9 px-4 py-2 text-xs font-medium text-white shadow-lg"
          >
            {{ toast.message }}
          </div>
        </transition>
      </aside>
    </div>
  </Teleport>

  <FilePreviewDialog v-model="previewOpen" :file="previewFile" />
</template>

<script setup>
import { computed, h, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import {
  createListResource,
  createResource,
  FileUploader,
} from 'frappe-ui'
import PaperclipIcon from './TextEditorFileExtension/PaperclipIcon.vue'
import FileThumb from './AttachmentsPanel/FileThumb.vue'
import FilePreviewDialog from './AttachmentsPanel/FilePreviewDialog.vue'

dayjs.extend(relativeTime)

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  pageId: { type: String, required: true },
  editor: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'update:count'])

const uploader = ref(null)
const dragActive = ref(false)
const deleteInFlight = ref(null)
const toast = ref({ visible: false, message: '' })
let toastTimer = null

// Two-stage mount:
// - renderTree: keeps the teleported subtree in the DOM while animating in
//   or out. When fully closed + transition done, we unmount so a closed
//   panel contributes zero to layout (no horizontal scroll).
// - visible: drives the CSS classes. We flip it on the next tick after
//   mount so the enter transition actually plays.
const renderTree = ref(props.modelValue)
const visible = ref(false)

const previewOpen = ref(false)
const previewFile = ref(null)

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      renderTree.value = true
      nextTick(() => {
        visible.value = true
        attachments.reload()
      })
    } else {
      visible.value = false
      // renderTree flips to false in onTransitionEnd after the slide out
    }
  },
  { immediate: true },
)

function onTransitionEnd(e) {
  if (e.propertyName !== 'transform') return
  if (!visible.value) renderTree.value = false
}

// --- Inline icons (kept tiny, no extra deps) ---
const UploadCloudIcon = iconComponent([
  { tag: 'path', attrs: { d: 'M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25' } },
  { tag: 'polyline', attrs: { points: '16 16 12 12 8 16' } },
  { tag: 'line', attrs: { x1: 12, y1: 12, x2: 12, y2: 21 } },
])
const EyeIcon = iconComponent([
  { tag: 'path', attrs: { d: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z' } },
  { tag: 'circle', attrs: { cx: 12, cy: 12, r: 3 } },
])
const PlusIcon = iconComponent([
  { tag: 'line', attrs: { x1: 12, y1: 5, x2: 12, y2: 19 } },
  { tag: 'line', attrs: { x1: 5, y1: 12, x2: 19, y2: 12 } },
])
const DownloadIcon = iconComponent([
  { tag: 'path', attrs: { d: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4' } },
  { tag: 'polyline', attrs: { points: '7 10 12 15 17 10' } },
  { tag: 'line', attrs: { x1: 12, y1: 15, x2: 12, y2: 3 } },
])
const TrashIcon = iconComponent([
  { tag: 'polyline', attrs: { points: '3 6 5 6 21 6' } },
  {
    tag: 'path',
    attrs: {
      d: 'M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2',
    },
  },
])

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

// --- Data ---
const attachments = createListResource({
  doctype: 'File',
  fields: [
    'name',
    'file_name',
    'file_url',
    'file_size',
    'file_type',
    'is_private',
    'creation',
    'owner',
  ],
  filters: {
    attached_to_doctype: 'GP Page',
    attached_to_name: props.pageId,
  },
  orderBy: 'creation desc',
  pageLength: 100,
  auto: true,
  realtime: true,
  cache: ['GP Page Attachments', props.pageId],
})

const deleteFile = createResource({
  url: 'frappe.client.delete',
  makeParams(name) {
    return { doctype: 'File', name }
  },
  onSuccess() {
    deleteInFlight.value = null
    attachments.reload()
    showToast('Attachment deleted')
  },
  onError() {
    deleteInFlight.value = null
    showToast('Could not delete attachment')
  },
})

const uploadArgs = computed(() => ({
  doctype: 'GP Page',
  docname: props.pageId,
  private: 1,
}))

const fileCount = computed(() => attachments.data?.length || 0)

const totalSizeLabel = computed(() => {
  if (!attachments.data?.length) return ''
  const total = attachments.data.reduce(
    (s, f) => s + (Number(f.file_size) || 0),
    0,
  )
  const formatted = formatBytes(total)
  return formatted ? `${formatted} total` : ''
})

watch(
  () => attachments.data,
  (val) => {
    emit('update:count', Array.isArray(val) ? val.length : 0)
  },
)

watch(
  () => props.pageId,
  (newId) => {
    if (!newId) return
    attachments.update({
      filters: {
        attached_to_doctype: 'GP Page',
        attached_to_name: newId,
      },
      cache: ['GP Page Attachments', newId],
    })
    attachments.reload()
  },
)

function close() {
  emit('update:modelValue', false)
}

function safeString(v) {
  if (v === null || v === undefined) return ''
  return typeof v === 'string' ? v : typeof v === 'number' ? String(v) : ''
}

function formatBytes(bytes) {
  const n = Number(bytes)
  if (!Number.isFinite(n) || n < 1) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(n) / Math.log(1024))
  const size = n / Math.pow(1024, i)
  return `${size.toFixed(size >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}

function formatRelative(ts) {
  if (!ts) return ''
  const d = dayjs(ts)
  return d.isValid() ? d.fromNow() : ''
}

function onDrop(e) {
  dragActive.value = false
  const files = e.dataTransfer?.files
  if (!files || !files.length) return
  const u = uploader.value
  if (!u) return
  u.onFileAdd({ target: { files: [files[0]] } })
}

function onUploadSuccess() {
  attachments.reload()
  showToast('File uploaded')
}

function onUploadFailure() {
  showToast('Upload failed')
}

function confirmDelete(file) {
  const ok = window.confirm(
    `Delete "${file.file_name}"? This cannot be undone.`,
  )
  if (!ok) return
  deleteInFlight.value = file.name
  deleteFile.submit(file.name)
}

function openPreview(file) {
  previewFile.value = file
  previewOpen.value = true
}

function isImageFile(file) {
  if (!file) return false
  const type = safeString(file.file_type).toLowerCase()
  if (type.startsWith('image/')) return true
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(type)) return true
  const name = safeString(file.file_name)
  return /\.(png|jpe?g|gif|webp|svg)$/i.test(name)
}

function insertIntoDoc(file) {
  if (!props.editor) return
  const editor = props.editor
  // Insert at the end of the document so we don't depend on the editor
  // already being focused, and so the insert is visible.
  const endPos = editor.state.doc.content.size
  if (isImageFile(file)) {
    editor
      .chain()
      .insertContentAt(endPos, {
        type: 'image',
        attrs: { src: file.file_url },
      })
      .run()
  } else {
    editor
      .chain()
      .insertContentAt(endPos, {
        type: 'file-attachment',
        attrs: {
          src: safeString(file.file_url),
          fileName: safeString(file.file_name),
          fileSize: Number(file.file_size) || 0,
          mimeType: safeString(file.file_type),
        },
      })
      .run()
  }
  // Explicitly blur so bubble/floating menus don't pop up on the empty
  // paragraph that TipTap adds after an atom block. No focus() was called,
  // so the editor should already not be focused — this is belt-and-braces.
  editor.commands.blur()
  showToast('Inserted into document')
}

function showToast(message) {
  toast.value.message = message
  toast.value.visible = true
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value.visible = false
  }, 2500)
}

onBeforeUnmount(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>
