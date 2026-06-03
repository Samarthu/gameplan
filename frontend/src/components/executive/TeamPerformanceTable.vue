<template>
  <div class="overflow-x-auto rounded-lg border bg-surface-white">
    <table class="min-w-full divide-y divide-outline-gray-2 text-sm">
      <thead class="bg-surface-gray-1">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            class="cursor-pointer px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-ink-gray-6"
            @click="sortBy(col.key)"
          >
            {{ col.label }}
            <span v-if="sortKey === col.key" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-outline-gray-2">
        <tr
          v-for="team in sortedTeams"
          :key="team.name"
          class="hover:bg-surface-gray-1"
        >
          <td class="px-4 py-3">
            <router-link
              :to="{ name: 'TeamOverview', params: { teamId: team.name } }"
              class="font-medium text-ink-gray-9 hover:underline"
            >
              {{ team.icon }} {{ team.title }}
            </router-link>
          </td>
          <td class="px-4 py-3">
            <HealthBadge :health="team.health" />
          </td>
          <td class="px-4 py-3">
            <div v-if="team.lead" class="flex items-center gap-2">
              <UserAvatar :user="team.lead" />
              <span class="text-ink-gray-8">{{ team.lead_name }}</span>
            </div>
            <span v-else class="font-medium text-red-700">Not assigned</span>
          </td>
          <td class="max-w-xs px-4 py-3 text-xs text-ink-gray-6">{{ team.insight || '—' }}</td>
          <td class="px-4 py-3 text-ink-gray-8">{{ team.metrics.overdue_count }}</td>
          <td class="px-4 py-3 text-ink-gray-8">{{ team.metrics.completed_7d }}</td>
          <td class="px-4 py-3 text-ink-gray-8">{{ team.metrics.stale_count }}</td>
          <td class="px-4 py-3 text-ink-gray-8">{{ team.metrics.at_risk_goals }}</td>
          <td class="px-4 py-3 text-ink-gray-8 max-w-[200px] truncate">
            <template v-if="team.worst_project">
              <router-link
                v-if="team.worst_project.name"
                :to="{
                  name: 'ProjectOverview',
                  params: { teamId: team.name, projectId: team.worst_project.name },
                }"
                class="hover:underline"
              >
                {{ team.worst_project.title }}
              </router-link>
              <span class="text-ink-gray-5"> ({{ team.worst_project.overdue_tasks }} overdue)</span>
            </template>
            <span v-else class="text-ink-gray-5">—</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="!teams.length" class="px-4 py-8 text-center text-ink-gray-5">
      No teams yet. Create Growth, Operations, CX, and Product teams aligned with the Operating System.
    </p>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import HealthBadge from './HealthBadge.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const props = defineProps({
  teams: { type: Array, default: () => [] },
})

const healthOrder = { red: 0, amber: 1, green: 2 }
const sortKey = ref('health')
const sortDir = ref('asc')

const columns = [
  { key: 'title', label: 'Team' },
  { key: 'health', label: 'Health' },
  { key: 'lead_name', label: 'Team lead' },
  { key: 'insight', label: 'Insight' },
  { key: 'overdue', label: 'Overdue' },
  { key: 'completed', label: 'Done (wk)' },
  { key: 'stale', label: 'Stale' },
  { key: 'at_risk', label: 'At-risk goals' },
  { key: 'worst', label: 'Worst project' },
]

function sortBy(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

const sortedTeams = computed(() => {
  const list = [...props.teams]
  const dir = sortDir.value === 'asc' ? 1 : -1
  list.sort((a, b) => {
    let av, bv
    switch (sortKey.value) {
      case 'health':
        av = healthOrder[a.health] ?? 9
        bv = healthOrder[b.health] ?? 9
        break
      case 'overdue':
        av = a.metrics?.overdue_count ?? 0
        bv = b.metrics?.overdue_count ?? 0
        break
      case 'stale':
        av = a.metrics?.stale_count ?? 0
        bv = b.metrics?.stale_count ?? 0
        break
      case 'at_risk':
        av = a.metrics?.at_risk_goals ?? 0
        bv = b.metrics?.at_risk_goals ?? 0
        break
      case 'lead_name':
        av = a.lead_name || ''
        bv = b.lead_name || ''
        return dir * av.localeCompare(bv)
      default:
        av = a.title || ''
        bv = b.title || ''
        return dir * av.localeCompare(bv)
    }
    return dir * (av - bv)
  })
  return list
})
</script>
