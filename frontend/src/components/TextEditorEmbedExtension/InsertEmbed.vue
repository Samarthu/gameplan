<template>
  <slot v-bind="{ onClick: openDialog }"></slot>
  <Dialog
    :options="{ title: 'Embed from the web' }"
    v-model="dialog.show"
    @after-leave="reset"
  >
    <template #body-content>
      <FormControl
        type="text"
        label="URL"
        placeholder="https://www.youtube.com/watch?v=..."
        v-model="dialog.url"
        @update:modelValue="dialog.error = ''"
        @keydown.enter.prevent="insert"
      />
      <p class="mt-2 text-xs text-ink-gray-5">
        Supports: {{ supported.join(', ') }}.
      </p>
      <p v-if="dialog.error" class="mt-2 text-sm text-ink-red-4">
        {{ dialog.error }}
      </p>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button variant="solid" @click="insert">Embed</Button>
        <Button @click="reset">Cancel</Button>
      </div>
    </template>
  </Dialog>
</template>

<script>
import { Button, Dialog, FormControl } from 'frappe-ui'
import { resolveEmbed, SUPPORTED_PROVIDERS } from './providers'

const defaultDialog = () => ({ show: false, url: '', error: '' })

export default {
  name: 'InsertEmbed',
  components: { Button, Dialog, FormControl },
  props: ['editor'],
  expose: ['openDialog'],
  data() {
    return { dialog: defaultDialog(), supported: SUPPORTED_PROVIDERS }
  },
  methods: {
    openDialog() {
      this.dialog.show = true
    },
    insert() {
      const url = (this.dialog.url || '').trim()
      if (!url) {
        this.dialog.error = 'Please paste a URL.'
        return
      }
      const resolved = resolveEmbed(url)
      if (!resolved) {
        this.dialog.error = 'Unsupported URL. Only YouTube, Vimeo, Loom, Figma, or Google Drive/Docs links are allowed.'
        return
      }
      this.editor.chain().focus().insertWebEmbed(url).run()
      this.dialog.show = false
    },
    reset() {
      this.dialog = defaultDialog()
    },
  },
}
</script>
