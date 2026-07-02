<template>
  <teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-20 bg-black-overlay-200 dark:backdrop-filter dark:backdrop-blur-[1px]"
    >
      <div class="absolute right-0 z-10 flex gap-2 p-4 text-right">
        <a :href="imageUrl" :download="downloadName" title="Download">
          <Button icon="download" />
        </a>
        <Button icon="x" @click="$emit('update:show', false)"> </Button>
      </div>
      <div
        class="flex h-full items-center justify-center"
        @click.self="$emit('update:show', false)"
      >
        <img :src="imageUrl" class="max-h-[80%] object-contain" />
      </div>
    </div>
  </teleport>
</template>
<script>
export default {
  name: 'ImagePreview',
  props: ['show', 'imageUrl'],
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
      if (this.show) {
        document.body.classList.add('overflow-hidden')
      } else {
        document.body.classList.remove('overflow-hidden')
      }
    },
  },
  methods: {
    handleEscape(e) {
      if (e.key === 'Escape') {
        this.$emit('update:show', false)
      }
    },
  },
}
</script>
