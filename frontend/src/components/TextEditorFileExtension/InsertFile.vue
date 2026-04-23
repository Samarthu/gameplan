<template>
  <slot v-bind="{ onClick: openDialog }"></slot>
  <Dialog
    :options="{ title: 'Attach a file' }"
    v-model="dialog.show"
    @after-leave="reset"
  >
    <template #body-content>
      <FileUploader @success="onUploadSuccess">
        <template v-slot="{ file, progress, uploading, openFileSelector, error }">
          <div class="flex flex-col gap-2">
            <div class="flex items-center space-x-2">
              <Button @click="openFileSelector">
                {{
                  uploading
                    ? `Uploading ${progress}%`
                    : dialog.fileUrl
                      ? 'Change File'
                      : 'Choose File'
                }}
              </Button>
              <Button v-if="dialog.fileUrl" @click="clearFile">Remove</Button>
            </div>
            <p v-if="error" class="text-sm text-ink-red-4">{{ error }}</p>
          </div>
        </template>
      </FileUploader>
      <div
        v-if="dialog.fileUrl"
        class="mt-3 flex items-center gap-3 rounded-md border border-outline-gray-modals bg-surface-gray-1 px-3 py-2"
      >
        <span class="flex-1 truncate text-sm text-ink-gray-8">
          {{ dialog.fileName }}
        </span>
        <span class="text-xs text-ink-gray-5">{{ formattedSize }}</span>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button
          variant="solid"
          :disabled="!dialog.fileUrl"
          @click="insert"
        >
          Insert
        </Button>
        <Button @click="reset">Cancel</Button>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { Button, Dialog, FileUploader } from 'frappe-ui'

function formatBytes(bytes) {
  if (!bytes || bytes < 1) return ''
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const size = bytes / Math.pow(1024, i)
  return `${size.toFixed(size >= 10 || i === 0 ? 0 : 1)} ${units[i]}`
}

const defaultDialog = () => ({
  show: false,
  fileUrl: '',
  fileName: '',
  fileSize: 0,
  mimeType: '',
})

export default {
  name: 'InsertFile',
  components: { Button, Dialog, FileUploader },
  props: ['editor'],
  expose: ['openDialog'],
  data() {
    return { dialog: defaultDialog() }
  },
  computed: {
    formattedSize() {
      return formatBytes(this.dialog.fileSize)
    },
  },
  methods: {
    openDialog() {
      this.dialog.show = true
    },
    onUploadSuccess(file) {
      this.dialog.fileUrl = file.file_url || ''
      this.dialog.fileName =
        file.file_name || (this.dialog.fileUrl ? this.dialog.fileUrl.split('/').pop() : '')
      this.dialog.fileSize = Number(file.file_size) || 0
      this.dialog.mimeType = file.content_type || file.file_type || ''
    },
    clearFile() {
      this.dialog.fileUrl = ''
      this.dialog.fileName = ''
      this.dialog.fileSize = 0
      this.dialog.mimeType = ''
    },
    insert() {
      if (!this.dialog.fileUrl) return
      this.editor
        .chain()
        .focus()
        .insertFileAttachment({
          src: this.dialog.fileUrl,
          fileName: this.dialog.fileName,
          fileSize: this.dialog.fileSize,
          mimeType: this.dialog.mimeType,
        })
        .run()
      this.dialog.show = false
    },
    reset() {
      this.dialog = defaultDialog()
    },
  },
}
</script>
