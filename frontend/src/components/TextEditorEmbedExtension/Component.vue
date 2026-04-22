<template>
  <node-view-wrapper class="web-embed my-4">
    <div
      v-if="isAllowed"
      class="relative w-full overflow-hidden rounded-lg border border-outline-gray-modals bg-surface-gray-1"
      :style="{ aspectRatio: aspectRatio }"
      contenteditable="false"
    >
      <iframe
        :src="src"
        :title="`Embedded ${provider || 'content'}`"
        class="absolute inset-0 h-full w-full"
        loading="lazy"
        allowfullscreen
        referrerpolicy="strict-origin-when-cross-origin"
        sandbox="allow-scripts allow-same-origin allow-popups allow-presentation allow-forms"
      />
    </div>
    <div
      v-else
      class="rounded-lg border border-dashed border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6"
      contenteditable="false"
    >
      Embed removed (source not allowed).
    </div>
  </node-view-wrapper>
</template>

<script>
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import { isAllowedEmbedSrc } from './providers'

export default {
  name: 'WebEmbedView',
  components: { NodeViewWrapper },
  props: nodeViewProps,
  computed: {
    src() {
      return this.node.attrs.src
    },
    provider() {
      return this.node.attrs.provider
    },
    aspectRatio() {
      return this.node.attrs.aspectRatio || '16 / 9'
    },
    isAllowed() {
      return isAllowedEmbedSrc(this.src)
    },
  },
}
</script>
