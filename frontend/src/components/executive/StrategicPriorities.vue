<template>
  <div class="overflow-x-auto rounded-lg border bg-surface-white">
    <table class="min-w-full divide-y divide-outline-gray-2 text-sm">
      <thead class="bg-surface-gray-1">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            class="px-4 py-3 text-xs font-medium uppercase tracking-wide text-ink-gray-6"
            :class="column.align === 'right' ? 'text-right' : 'text-left'"
          >
            <span class="inline-flex items-center gap-1">
              {{ column.label }}
              <InfoTooltip :text="column.info" :label="column.label" />
            </span>
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-outline-gray-2">
        <tr v-for="item in priorities" :key="item.name" class="hover:bg-surface-gray-1">
          <td class="max-w-xs px-4 py-3">
            <router-link
              :to="{ name: 'ProjectOverview', params: { teamId: item.team, projectId: item.name } }"
              class="font-medium text-ink-gray-9 hover:underline"
            >
              {{ item.title }}
            </router-link>
            <p class="mt-0.5 truncate text-xs text-ink-gray-5">
              {{ item.team_icon }} {{ item.team_title }}
              <span v-if="item.days_since_update != null"> · updated {{ item.days_since_update }}d ago</span>
            </p>
          </td>
          <td class="px-4 py-3">
            <div v-if="item.lead" class="flex items-center gap-2">
              <UserAvatar :user="item.lead" />
              <span class="text-ink-gray-8">{{ item.lead_name || item.lead }}</span>
            </div>
            <span v-else class="font-medium text-red-700">No owner</span>
          </td>
          <td class="px-4 py-3"><HealthBadge :health="item.health" /></td>
          <td class="px-4 py-3 text-right font-medium text-ink-gray-8">{{ item.progress }}%</td>
          <td class="px-4 py-3 text-right text-ink-gray-8">
            {{ item.done_goals }}/{{ item.goals_total }}
            <span v-if="item.at_risk_goals" class="ml-1 text-red-700">({{ item.at_risk_goals }} risk)</span>
          </td>
          <td class="px-4 py-3 text-right font-medium" :class="item.overdue_tasks ? 'text-red-700' : 'text-ink-gray-8'">
            {{ item.overdue_tasks }}
          </td>
          <td class="px-4 py-3 text-right text-ink-gray-8">{{ item.completed_week }}</td>
          <td class="max-w-sm px-4 py-3 text-xs text-ink-gray-6">{{ item.decision_needed }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!priorities.length" class="px-4 py-8 text-center text-sm text-ink-gray-5">
      No open strategic priorities found.
    </p>
  </div>
</template>

<script setup>
import HealthBadge from './HealthBadge.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import InfoTooltip from './InfoTooltip.vue'

defineProps({
  priorities: { type: Array, default: () => [] },
})

const columns = [
  {
    key: 'priority',
    label: 'Priority',
    info: 'Open project or initiative ranked by strategic risk and operating discipline.',
  },
  {
    key: 'owner',
    label: 'Owner',
    info: 'Team Lead accountable for this priority. No owner means CEO cannot hold anyone clearly accountable.',
  },
  {
    key: 'health',
    label: 'Health',
    info: 'Risk status based on at-risk goals, overdue work, stale work, low progress, and old updates.',
  },
  {
    key: 'progress',
    label: 'Progress',
    align: 'right',
    info: 'Project progress percentage calculated from completed tasks in the project.',
  },
  {
    key: 'goals',
    label: 'Goals',
    align: 'right',
    info: 'Completed goals over total project goals. 0/0 means the business outcome has not been defined.',
  },
  {
    key: 'overdue',
    label: 'Overdue',
    align: 'right',
    info: 'Open tasks in this priority that are past their due date.',
  },
  {
    key: 'done',
    label: 'Done wk',
    align: 'right',
    info: 'Tasks completed for this priority during the selected week.',
  },
  {
    key: 'decision',
    label: 'Decision',
    info: 'Recommended leadership action, such as assigning an owner, defining goals, unblocking work, or reviewing scope.',
  },
]
</script>
