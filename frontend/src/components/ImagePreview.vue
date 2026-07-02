<template>
  <teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex flex-col bg-black/80">
      <div class="flex justify-end p-4">
        <Button icon="x" @click="close" />
      </div>
      <div
        class="flex min-h-0 flex-1 items-center justify-center overflow-auto p-4"
        @click.self="close"
        @wheel.prevent="onWheel"
      >
        <img
          :src="imageUrl"
          class="max-h-full max-w-full object-contain transition-transform duration-100"
          :style="{ transform: `scale(${scale})` }"
        />
      </div>
      <div class="flex justify-center p-4">
        <div class="flex items-center gap-1 rounded-lg bg-surface-white px-2 py-1.5 shadow-lg">
          <Button variant="ghost" icon="zoom-out" :disabled="scale <= MIN_SCALE" @click="zoomOut" title="Zoom out" />
          <button
            class="w-14 rounded px-1 text-center text-sm tabular-nums text-ink-gray-7 hover:bg-surface-gray-2"
            title="Reset zoom"
            @click="scale = 1"
          >
            {{ Math.round(scale * 100) }}%
          </button>
          <Button variant="ghost" icon="zoom-in" :disabled="scale >= MAX_SCALE" @click="zoomIn" title="Zoom in" />
          <div class="mx-1 h-5 w-px bg-outline-gray-2"></div>
          <a :href="imageUrl" :download="downloadName" title="Download">
            <Button variant="ghost" icon="download" />
          </a>
        </div>
      </div>
    </div>
  </teleport>
</template>
<script>
const MIN_SCALE = 0.25
const MAX_SCALE = 5

export default {
  name: 'ImagePreview',
  props: ['show', 'imageUrl'],
  data() {
    return { scale: 1, MIN_SCALE, MAX_SCALE }
  },
  computed: {
    downloadName() {
      try {
        return decodeURIComponent(new URL(this.imageUrl, window.location.origin).pathname.split('/').pop())
      } catch {
        return 'image'
      }
    },
  },
  mounted() {
    document.addEventListener('keyup', this.handleEscape)
  },
  beforeUnmount() {
    document.removeEventListener('keyup', this.handleEscape)
  },
  watch: {
    show() {
      this.scale = 1
      if (this.show) {
        document.body.classList.add('overflow-hidden')
      } else {
        document.body.classList.remove('overflow-hidden')
      }
    },
  },
  methods: {
    close() {
      this.$emit('update:show', false)
    },
    clampScale(value) {
      return Math.min(MAX_SCALE, Math.max(MIN_SCALE, value))
    },
    zoomIn() {
      this.scale = this.clampScale(this.scale * 1.25)
    },
    zoomOut() {
      this.scale = this.clampScale(this.scale / 1.25)
    },
    onWheel(e) {
      this.scale = this.clampScale(this.scale * (e.deltaY < 0 ? 1.1 : 0.9))
    },
    handleEscape(e) {
      if (e.key === 'Escape') {
        this.close()
      }
    },
  },
}
</script>
