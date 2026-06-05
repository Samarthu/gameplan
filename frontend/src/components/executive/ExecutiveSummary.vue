<template>
  <div>
    <div class="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-8">
      <button
        v-for="card in cards"
        :key="card.key"
        type="button"
        class="rounded-lg border bg-surface-white px-4 py-3 text-left transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        :class="[
          card.borderClass,
          card.clickable ? 'cursor-pointer hover:border-outline-gray-3' : 'cursor-default opacity-90',
        ]"
        :disabled="!card.clickable"
        @click="openDrilldown(card)"
      >
        <div class="flex items-start justify-between gap-2">
          <p class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">{{ card.label }}</p>
          <InfoTooltip :text="card.info" :label="card.label" />
        </div>
        <p class="mt-1 text-2xl font-semibold" :class="card.valueClass">{{ card.value }}</p>
        <p v-if="card.hint" class="mt-1 text-xs text-ink-gray-6">{{ card.hint }}</p>
        <p v-if="card.clickable" class="mt-2 text-[10px] font-medium uppercase tracking-wide text-ink-gray-4">
          Click for details
        </p>
      </button>
    </div>

    <ExecutiveSummaryDetailDialog
      v-model="dialogOpen"
      :drilldown="activeDrilldown"
      :title="dialogTitle"
      :description="dialogDescription"
      :items="dialogItems"
      :teams="teams"
      :escalations="escalations"
      :unassigned-overdue="summary.unassigned_overdue || 0"
    />
  </div>
</template>
<script setup>
import { computed, ref } from 'vue'
import ExecutiveSummaryDetailDialog from './ExecutiveSummaryDetailDialog.vue'
import InfoTooltip from './InfoTooltip.vue'

const props = defineProps({
  summary: { type: Object, default: () => ({}) },
  teams: { type: Array, default: () => [] },
  people: { type: Array, default: () => [] },
  leadAccountability: { type: Array, default: () => [] },
  escalations: { type: Array, default: () => [] },
})

const dialogOpen = ref(false)
const activeDrilldown = ref('')
const dialogTitle = ref('')
const dialogDescription = ref('')
const dialogItems = ref([])

const cards = computed(() => {
  const s = props.summary || {}
  const peopleTotal = (s.people_underperforming ?? 0) + (s.people_struggling ?? 0)
  return [
    {
      key: 'decisions_pending',
      label: 'Decisions',
      value: s.decisions_pending ?? 0,
      hint: 'Need leadership',
      valueClass: s.decisions_pending ? 'text-red-700' : 'text-ink-gray-9',
      borderClass: s.decisions_pending ? 'border-red-200' : '',
      clickable: false,
      info: 'Leadership decisions required before review, such as assigning owners, defining outcomes, resolving stale priorities, or unblocking urgent work.',
    },
    {
      key: 'strategic_risk',
      label: 'Priority risk',
      value: (s.strategic_priorities_red ?? 0) + (s.strategic_priorities_amber ?? 0),
      hint: `${s.strategic_priorities_red ?? 0} red`,
      valueClass: s.strategic_priorities_red ? 'text-red-700' : 'text-amber-800',
      borderClass: s.strategic_priorities_red ? 'border-red-200' : 'border-amber-200',
      clickable: false,
      info: 'Open projects or initiatives that are red or amber because of missing ownership, at-risk goals, stale updates, low progress, overdue work, or missing goals.',
    },
    {
      key: 'teams_red',
      label: 'Teams in red',
      value: s.teams_red ?? 0,
      hint: 'Act in Monday review',
      valueClass: s.teams_red ? 'text-red-700' : 'text-ink-gray-9',
      borderClass: s.teams_red ? 'border-red-200' : '',
      clickable: (s.teams_red ?? 0) > 0,
      info: 'Teams in critical health. A team turns red when overdue work, at-risk goals, or sprint slip crosses the configured thresholds.',
    },
    {
      key: 'leads_at_risk',
      label: 'Leads at risk',
      value: s.leads_underperforming ?? 0,
      hint: 'Missing lead or red team',
      valueClass: s.leads_underperforming ? 'text-red-700' : 'text-ink-gray-9',
      borderClass: s.leads_underperforming ? 'border-red-200' : '',
      clickable: (s.leads_underperforming ?? 0) > 0,
      info: 'Team leads accountable for red/amber delivery, plus teams where leadership ownership is missing.',
    },
    {
      key: 'no_team_lead',
      label: 'No team lead',
      value: s.teams_without_lead ?? 0,
      hint: 'Assign on team page',
      valueClass: s.teams_without_lead ? 'text-amber-800' : 'text-ink-gray-9',
      borderClass: s.teams_without_lead ? 'border-amber-200' : '',
      clickable: (s.teams_without_lead ?? 0) > 0,
      info: 'Teams without an assigned Team Lead. These need ownership before execution accountability is clear.',
    },
    {
      key: 'people_behind',
      label: 'People behind',
      value: peopleTotal,
      hint: `${s.people_underperforming ?? 0} critical`,
      valueClass: (s.people_underperforming ?? 0) > 0 ? 'text-red-700' : 'text-ink-gray-9',
      borderClass: (s.people_underperforming ?? 0) > 0 ? 'border-red-200' : '',
      clickable: peopleTotal > 0,
      info: 'People with the heaviest overdue workload, grouped as critical or struggling based on overdue, stale, and completed work.',
    },
    {
      key: 'overdue_tasks',
      label: 'Overdue tasks',
      value: s.total_overdue ?? 0,
      hint: s.unassigned_overdue ? `${s.unassigned_overdue} unassigned` : '',
      valueClass: 'text-ink-gray-9',
      borderClass: '',
      clickable: (s.total_overdue ?? 0) > 0,
      info: 'Open tasks past their due date across all teams. The hint calls out overdue tasks that have no assignee.',
    },
    {
      key: 'closed_week',
      label: 'Closed this week',
      value: s.total_completed_week ?? 0,
      hint: 'Org-wide completions',
      valueClass: 'text-green-800',
      borderClass: 'border-green-200',
      clickable: true,
      info: 'Tasks completed during the selected week across the organization.',
    },
  ]
})

function openDrilldown(card) {
  if (!card.clickable && card.key !== 'closed_week') return

  activeDrilldown.value = card.key
  dialogTitle.value = card.label
  dialogDescription.value = ''

  switch (card.key) {
    case 'teams_red':
      dialogDescription.value =
        'Teams in critical health — discuss in Monday review and assign clear owners.'
      dialogItems.value = props.teams.filter((t) => t.health === 'red')
      break
    case 'leads_at_risk':
      dialogDescription.value =
        'Team leads accountable for missing leadership or poor team delivery this week.'
      dialogItems.value = props.leadAccountability.length
        ? props.leadAccountability
        : props.teams.filter(
            (t) => t.accountability === 'missing_lead' || t.accountability === 'underperforming'
          )
      break
    case 'no_team_lead':
      dialogDescription.value = 'Assign a Team Lead on each team’s Overview page.'
      dialogItems.value = props.teams.filter((t) => !t.lead)
      break
    case 'people_behind':
      dialogDescription.value =
        'Individuals with overdue workload — use for 1:1s and re-prioritization.'
      dialogItems.value = props.people
      break
    case 'overdue_tasks':
      dialogDescription.value = 'Overdue work by team and the most urgent tasks.'
      dialogItems.value = []
      break
    case 'closed_week':
      dialogDescription.value = 'Tasks completed during the selected week, by team.'
      dialogItems.value = props.teams
        .filter((t) => (t.metrics?.completed_7d || 0) > 0)
        .sort((a, b) => (b.metrics?.completed_7d || 0) - (a.metrics?.completed_7d || 0))
      break
    default:
      dialogItems.value = []
  }

  dialogOpen.value = true
}
</script>
