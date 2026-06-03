<template>
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
    <router-link
      v-for="team in teams"
      :key="team.name"
      :to="{ name: 'TeamOverview', params: { teamId: team.name } }"
      class="rounded-lg border bg-surface-white p-4 shadow-sm transition hover:border-outline-gray-3 hover:shadow-md"
    >
      <div class="flex items-start justify-between gap-2">
        <div class="flex items-center gap-2 min-w-0">
          <span class="text-xl shrink-0">{{ team.icon }}</span>
          <h3 class="font-semibold text-ink-gray-9 truncate">{{ team.title }}</h3>
          <LucideLock v-if="team.is_private" class="h-3 w-3 shrink-0 text-ink-gray-5" />
        </div>
        <HealthBadge :health="team.health" />
      </div>
      <div class="mt-3 flex items-center gap-2 text-sm">
        <UserAvatar v-if="team.lead" :user="team.lead" />
        <div class="min-w-0">
          <p class="text-xs text-ink-gray-5">Team lead</p>
          <p
            class="font-medium truncate"
            :class="team.lead ? 'text-ink-gray-8' : 'text-red-700'"
          >
            {{ team.lead_name || 'Not assigned' }}
          </p>
        </div>
      </div>
      <p
        v-if="team.insight"
        class="mt-3 text-xs leading-relaxed"
        :class="team.accountability === 'underperforming' || team.accountability === 'missing_lead' ? 'text-red-800' : 'text-ink-gray-6'"
      >
        {{ team.insight }}
      </p>
      <dl class="mt-4 grid grid-cols-2 gap-x-3 gap-y-2 text-xs text-ink-gray-6">
        <div>
          <dt class="text-ink-gray-5">Overdue</dt>
          <dd class="font-semibold text-ink-gray-9">{{ team.metrics.overdue_count }}</dd>
        </div>
        <div>
          <dt class="text-ink-gray-5">Stale</dt>
          <dd class="font-semibold text-ink-gray-9">{{ team.metrics.stale_count }}</dd>
        </div>
        <div>
          <dt class="text-ink-gray-5">Done (week)</dt>
          <dd class="font-semibold text-ink-gray-9">{{ team.metrics.completed_7d }}</dd>
        </div>
        <div>
          <dt class="text-ink-gray-5">Goals at risk</dt>
          <dd class="font-semibold text-ink-gray-9">{{ team.metrics.at_risk_goals }}</dd>
        </div>
      </dl>
      <p v-if="team.active_sprint" class="mt-3 text-xs text-ink-gray-6 line-clamp-2">
        Sprint: {{ team.active_sprint.title }}
        <span v-if="team.active_sprint.end_date"> · ends {{ formatDate(team.active_sprint.end_date) }}</span>
        · {{ team.active_sprint.completion_pct }}% done
      </p>
    </router-link>
  </div>
</template>
<script setup>
import dayjs from '@/utils/dayjs'
import HealthBadge from './HealthBadge.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import LucideLock from '~icons/lucide/lock'

defineProps({
  teams: { type: Array, default: () => [] },
})

function formatDate(d) {
  return d ? dayjs(d).format('D MMM') : ''
}
</script>
