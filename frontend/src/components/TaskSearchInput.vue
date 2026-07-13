<template>
  <div class="relative w-56">
    <LucideSearch class="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-gray-4" />
    <input
      :value="modelValue"
      type="text"
      placeholder="Search by title or description"
      class="h-8 w-full rounded-lg border border-outline-gray-2 bg-surface-white pl-8 pr-8 text-sm text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
      @input="$emit('update:modelValue', $event.target.value.trim())"
    />
    <button
      v-if="modelValue"
      type="button"
      class="absolute right-2 top-1/2 -translate-y-1/2 text-ink-gray-5 hover:text-ink-gray-8"
      aria-label="Clear search"
      @click="$emit('update:modelValue', '')"
    >
      <LucideX class="h-4 w-4" />
    </button>
  </div>
</template>
<script setup>
defineProps({ modelValue: { type: String, default: '' } })
defineEmits(['update:modelValue'])
</script>
