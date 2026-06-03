<template>
  <span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize"
    :class="classes"
  >
    {{ health }}
  </span>
</template>
<script setup>
import { computed } from 'vue'

const props = defineProps({
  health: { type: String, default: 'green' },
})

const classes = computed(() => {
  if (props.health === 'red') {
    return 'bg-red-100 text-red-800'
  }
  if (props.health === 'amber') {
    return 'bg-amber-100 text-amber-900'
  }
  return 'bg-green-100 text-green-800'
})
</script>
