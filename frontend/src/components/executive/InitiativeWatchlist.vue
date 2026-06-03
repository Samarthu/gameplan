<template>
  <div class="space-y-3">
    <div
      v-for="item in initiatives"
      :key="item.name"
      class="flex flex-col gap-2 rounded-lg border bg-surface-white p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="min-w-0">
        <router-link
          :to="{
            name: 'ProjectOverview',
            params: { teamId: item.team, projectId: item.name },
          }"
          class="font-semibold text-ink-gray-9 hover:underline"
        >
          {{ item.title }}
        </router-link>
        <p class="mt-1 text-sm text-ink-gray-6">
          {{ item.overdue_tasks }} overdue task{{ item.overdue_tasks === 1 ? '' : 's' }}
          <span v-if="item.at_risk_goals"> · {{ item.at_risk_goals }} goal(s) at risk</span>
          · {{ item.progress }}% progress
        </p>
        <ul v-if="item.goals?.length" class="mt-2 flex flex-wrap gap-2">
          <li
            v-for="(goal, idx) in item.goals"
            :key="idx"
            class="rounded px-2 py-0.5 text-xs"
            :class="
              goal.status === 'At Risk'
                ? 'bg-amber-100 text-amber-900'
                : goal.status === 'Done'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-surface-gray-2 text-ink-gray-7'
            "
          >
            {{ goal.title }} — {{ goal.status }}
          </li>
        </ul>
      </div>
      <Button
        variant="outline"
        :route="{
          name: 'ProjectTasks',
          params: { teamId: item.team, projectId: item.name },
        }"
      >
        View tasks
      </Button>
    </div>
    <p v-if="!initiatives.length" class="rounded-lg border border-dashed px-4 py-8 text-center text-sm text-ink-gray-5">
      No initiatives need attention this week.
    </p>
  </div>
</template>
<script setup>
import { Button } from 'frappe-ui'

defineProps({
  initiatives: { type: Array, default: () => [] },
})
</script>
