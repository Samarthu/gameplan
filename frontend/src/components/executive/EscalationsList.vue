<template>
  <ul class="divide-y divide-outline-gray-2 rounded-lg border bg-surface-white">
    <li
      v-for="(item, idx) in escalations"
      :key="idx"
      class="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="flex min-w-0 items-start gap-3">
        <HealthBadge :health="item.health || 'amber'" />
        <div class="min-w-0">
          <p class="font-medium text-ink-gray-9">{{ item.title }}</p>
          <p class="text-xs text-ink-gray-5 capitalize">{{ typeLabel(item.type) }}</p>
          <p v-if="item.days_late != null" class="text-xs text-red-700">{{ item.days_late }} days overdue</p>
        </div>
      </div>
      <div class="flex shrink-0 gap-2">
        <Button
          v-if="item.task && item.team"
          size="sm"
          variant="outline"
          :route="{
            name: 'Task',
            params: { taskId: item.task },
            query: item.team ? { team: item.team } : {},
          }"
        >
          Open task
        </Button>
        <Button
          v-else-if="item.project && item.team"
          size="sm"
          variant="outline"
          :route="{
            name: 'ProjectOverview',
            params: { teamId: item.team, projectId: item.project },
          }"
        >
          Open project
        </Button>
        <Button
          v-else-if="item.team"
          size="sm"
          variant="outline"
          :route="{ name: 'TeamOverview', params: { teamId: item.team } }"
        >
          Open team
        </Button>
      </div>
    </li>
  </ul>
  <p v-if="!escalations.length" class="mt-3 text-sm text-ink-gray-5">No escalations right now.</p>
</template>
<script setup>
import { Button } from 'frappe-ui'
import HealthBadge from './HealthBadge.vue'

defineProps({
  escalations: { type: Array, default: () => [] },
})

function typeLabel(type) {
  const map = {
    team_red: 'Team escalation',
    goal_at_risk: 'Goal at risk',
    overdue_task: 'Overdue task',
  }
  return map[type] || type
}
</script>
