<template>
  <Tooltip :text="text">
    <button
      type="button"
      class="inline-flex h-5 w-5 items-center justify-center rounded-full text-ink-gray-4 hover:bg-surface-gray-2 hover:text-ink-gray-7 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      :aria-label="ariaLabel"
      @click.stop
    >
      <LucideInfo class="h-3.5 w-3.5" />
    </button>
  </Tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'
import LucideInfo from '~icons/lucide/info'

const props = defineProps({
  text: { type: String, required: true },
  label: { type: String, default: '' },
})

const ariaLabel = computed(() => props.label ? `About ${props.label}` : 'More information')
</script>
