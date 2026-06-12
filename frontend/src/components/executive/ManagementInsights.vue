<template>
  <ul class="space-y-2 rounded-lg border border-amber-200 bg-amber-50/50 px-4 py-3">
    <li
      v-for="(item, idx) in insights"
      :key="idx"
      class="flex items-start gap-2 text-sm"
    >
      <span
        class="mt-1.5 h-2 w-2 shrink-0 rounded-full"
        :class="severityDot(item.severity)"
      />
      <span class="text-ink-gray-8">{{ item.text }}</span>
    </li>
  </ul>
</template>
<script setup>
defineProps({
  insights: { type: Array, default: () => [] },
})

function severityDot(severity) {
  if (severity === 'red') return 'bg-red-600'
  if (severity === 'amber') return 'bg-amber-500'
  if (severity === 'green') return 'bg-green-600'
  return 'bg-ink-gray-4'
}
</script>
