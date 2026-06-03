<template>
  <div class="overflow-x-auto rounded-lg border bg-surface-white">
    <table class="min-w-full divide-y divide-outline-gray-2 text-sm">
      <thead class="bg-surface-gray-1">
        <tr>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Team</th>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Team lead</th>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Status</th>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Management insight</th>
          <th class="px-4 py-3 text-right text-xs font-medium uppercase text-ink-gray-6">Overdue</th>
          <th class="px-4 py-3 text-right text-xs font-medium uppercase text-ink-gray-6">Done (wk)</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-outline-gray-2">
        <tr v-for="row in leads" :key="row.team" class="hover:bg-surface-gray-1">
          <td class="px-4 py-3">
            <router-link
              :to="{ name: 'TeamOverview', params: { teamId: row.team } }"
              class="font-medium text-ink-gray-9 hover:underline"
            >
              {{ row.team_icon }} {{ row.team_title }}
            </router-link>
          </td>
          <td class="px-4 py-3">
            <div v-if="row.lead" class="flex items-center gap-2">
              <UserAvatar :user="row.lead" />
              <span class="text-ink-gray-8">{{ row.lead_name }}</span>
            </div>
            <span v-else class="font-medium text-red-700">Not assigned</span>
          </td>
          <td class="px-4 py-3">
            <HealthBadge :health="row.health" />
            <span class="ml-2 text-xs capitalize text-ink-gray-6">{{ accountabilityLabel(row.accountability) }}</span>
          </td>
          <td class="max-w-md px-4 py-3 text-ink-gray-7">{{ row.insight }}</td>
          <td class="px-4 py-3 text-right font-medium text-ink-gray-9">
            {{ row.metrics?.overdue_count ?? 0 }}
          </td>
          <td class="px-4 py-3 text-right text-ink-gray-8">
            {{ row.metrics?.completed_7d ?? 0 }}
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!leads.length" class="px-4 py-8 text-center text-sm text-green-800">
      All team leads are on track this week.
    </p>
  </div>
</template>
<script setup>
import HealthBadge from './HealthBadge.vue'
import UserAvatar from '@/components/UserAvatar.vue'

defineProps({
  leads: { type: Array, default: () => [] },
})

function accountabilityLabel(acc) {
  const map = {
    missing_lead: 'No lead',
    underperforming: 'Underperforming',
    watch: 'Watch',
  }
  return map[acc] || acc
}
</script>
