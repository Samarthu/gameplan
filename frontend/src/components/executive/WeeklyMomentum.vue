<template>
  <div class="grid grid-cols-2 gap-3 lg:grid-cols-6">
    <div
      v-for="item in items"
      :key="item.key"
      class="rounded-lg border bg-surface-white px-3 py-2.5"
      :class="item.border"
    >
      <div class="flex items-start justify-between gap-2">
        <p class="text-[11px] font-medium uppercase tracking-wide text-ink-gray-5">{{ item.label }}</p>
        <InfoTooltip :text="item.info" :label="item.label" />
      </div>
      <p class="mt-1 text-xl font-semibold" :class="item.valueClass">{{ item.value }}</p>
      <p class="mt-0.5 text-xs text-ink-gray-5">{{ item.hint }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import InfoTooltip from './InfoTooltip.vue'

const props = defineProps({
  momentum: { type: Object, default: () => ({}) },
})

const items = computed(() => {
  const m = props.momentum || {}
  const net = Number(m.net_flow || 0)
  return [
    {
      key: 'opened',
      label: 'Opened',
      value: m.created_week ?? 0,
      hint: 'Tasks added this week',
      info: 'New tasks created during the selected week. This shows how much new work entered the system.',
    },
    {
      key: 'closed',
      label: 'Closed',
      value: m.completed_week ?? 0,
      hint: 'Tasks completed this week',
      valueClass: 'text-green-800',
      border: 'border-green-100',
      info: 'Tasks completed during the selected week. This is the weekly execution output.',
    },
    {
      key: 'net',
      label: 'Net flow',
      value: net > 0 ? `+${net}` : net,
      hint: net >= 0 ? 'Closed more than opened' : 'Backlog grew',
      valueClass: net >= 0 ? 'text-green-800' : 'text-amber-800',
      border: net >= 0 ? 'border-green-100' : 'border-amber-200',
      info: 'Closed tasks minus newly opened tasks. Negative means the backlog grew; positive means the team closed more than it added.',
    },
    {
      key: 'open',
      label: 'Open work',
      value: m.open_total ?? 0,
      hint: 'Current active backlog',
      info: 'All currently open, unfinished tasks across active teams.',
    },
    {
      key: 'overdue',
      label: 'Overdue',
      value: m.overdue_total ?? 0,
      hint: `${m.urgent_high_overdue ?? 0} urgent/high`,
      valueClass: m.overdue_total ? 'text-red-700' : 'text-ink-gray-9',
      border: m.overdue_total ? 'border-red-200' : '',
      info: 'Open tasks past their due date. The hint shows how many overdue tasks are urgent or high priority.',
    },
    {
      key: 'due',
      label: 'Due this week',
      value: m.due_this_week_open ?? 0,
      hint: `${m.completion_ratio ?? 0}% close/open ratio`,
      info: 'Open tasks due within the selected week. The ratio compares closed work against new work created this week.',
    },
  ]
})
</script>
