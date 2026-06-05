<template>
  <div class="rounded-lg border bg-surface-white">
    <div class="flex items-center justify-between border-b px-4 py-3">
      <div>
        <div class="flex items-center gap-1.5">
          <h2 class="text-base font-semibold text-ink-gray-9">Decisions required</h2>
          <InfoTooltip
            label="Decisions required"
            text="Leadership action queue. These are issues that need a CEO or manager decision, such as assigning ownership, defining outcomes, reviewing scope, or unblocking urgent overdue work."
          />
        </div>
        <p class="text-xs text-ink-gray-5">Items that need leadership action, not just task follow-up.</p>
      </div>
      <span class="rounded-full bg-surface-gray-2 px-2 py-0.5 text-xs font-medium text-ink-gray-7">
        {{ decisions.length }}
      </span>
    </div>

    <ul v-if="decisions.length" class="divide-y divide-outline-gray-2">
      <li
        v-for="item in decisions"
        :key="`${item.type}-${item.team || ''}-${item.project || ''}-${item.task || ''}-${item.title}`"
        class="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <HealthBadge :health="item.severity || 'amber'" />
            <p class="truncate font-medium text-ink-gray-9">{{ item.title }}</p>
          </div>
          <p class="mt-1 text-sm text-ink-gray-7">{{ item.action }}</p>
          <p v-if="item.meta" class="mt-0.5 text-xs text-ink-gray-5">{{ item.meta }}</p>
        </div>
        <Button v-if="routeFor(item)" size="sm" variant="outline" :route="routeFor(item)">
          Open
        </Button>
      </li>
    </ul>

    <p v-else class="px-4 py-8 text-center text-sm text-ink-gray-5">
      No leadership decisions required right now.
    </p>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import HealthBadge from './HealthBadge.vue'
import InfoTooltip from './InfoTooltip.vue'

defineProps({
  decisions: { type: Array, default: () => [] },
})

function routeFor(item) {
  if (item.task) {
    return { name: 'Task', params: { taskId: item.task }, query: item.team ? { team: item.team } : {} }
  }
  if (item.project && item.team) {
    return { name: 'ProjectOverview', params: { teamId: item.team, projectId: item.project } }
  }
  if (item.team) {
    return { name: 'TeamOverview', params: { teamId: item.team } }
  }
  return null
}
</script>
