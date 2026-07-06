<template>
  <div>
    <header
      class="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b bg-surface-white px-3 py-2.5 sm:px-5"
    >
      <Breadcrumbs
        :items="[{ label: 'Executive Cockpit', route: { name: 'ExecutiveCockpit' } }]"
      />
      <div class="flex flex-wrap items-center gap-2">
        <FormControl
          type="date"
          class="w-40"
          :modelValue="weekStartInput"
          label="Week starting"
          @update:modelValue="onWeekChange"
        />
        <Button variant="outline" :loading="executiveCockpit.loading" @click="reload">
          Refresh
        </Button>
        <a
          v-if="links.control_dashboard"
          :href="links.control_dashboard"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button variant="outline">Control Dashboard</Button>
        </a>
        <a
          v-if="links.weekly_scorecard"
          :href="links.weekly_scorecard"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button variant="outline">Weekly Scorecard</Button>
        </a>
      </div>
    </header>

    <div v-if="executiveCockpit.loading && !executiveCockpit.data" class="px-5 py-20 text-center text-ink-gray-5">
      Loading executive cockpit…
    </div>
    <div v-else-if="executiveCockpit.error" class="px-5 py-20 text-center text-red-700">
      <p>{{ executiveCockpit.error?.message || executiveCockpit.error || 'Failed to load dashboard' }}</p>
      <p class="mt-2 text-sm text-ink-gray-6">
        Run <code class="rounded bg-surface-gray-2 px-1">bench migrate</code> on the site if this page was just deployed.
      </p>
      <Button class="mt-4" variant="outline" @click="reload">Retry</Button>
    </div>
    <div v-else-if="!executiveCockpit.data" class="px-5 py-20 text-center text-ink-gray-5">
      No dashboard data returned.
      <Button class="mt-4" variant="outline" @click="reload">Retry</Button>
    </div>
    <div v-else class="mx-auto w-full max-w-7xl space-y-8 px-3 py-6 sm:px-5">
      <div>
        <h1 class="text-2xl font-semibold text-ink-gray-9">Executive Cockpit</h1>
        <p class="mt-1 text-sm text-ink-gray-6">
          Management view · Week {{ weekLabel }}
          <span v-if="generatedAt"> · Updated {{ generatedAt }}</span>
        </p>
      </div>

      <ExecutiveSummary
        :summary="summary"
        :teams="teams"
        :people="people"
        :lead-accountability="leadAccountability"
        :escalations="escalations"
      />

      <WeeklyMomentum :momentum="weeklyMomentum" />

      <div class="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.72fr)]">
        <section>
          <div class="mb-3 flex items-end justify-between gap-3">
            <div>
              <div class="flex items-center gap-1.5">
                <h2 class="text-lg font-semibold text-ink-gray-9">Strategic priorities</h2>
                <InfoTooltip
                  label="Strategic priorities"
                  text="Open projects ranked by CEO risk: ownership, goals, stale updates, progress, overdue work, and weekly movement."
                />
              </div>
              <p class="mt-1 text-sm text-ink-gray-6">
                Open initiatives ranked by outcome risk, ownership, update discipline, and weekly movement.
              </p>
            </div>
          </div>
          <StrategicPriorities :priorities="strategicPriorities" />
        </section>

        <DecisionQueue :decisions="decisionsRequired" />
      </div>

      <section v-if="managementInsights.length">
        <div class="mb-3 flex items-center gap-1.5">
          <h2 class="text-lg font-semibold text-ink-gray-9">CEO insights</h2>
          <InfoTooltip
            label="CEO insights"
            text="Auto-generated executive summary of the most important patterns across priorities, decisions, ownership, overdue work, and weekly movement."
          />
        </div>
        <p class="mb-3 text-sm text-ink-gray-6">
          Auto-generated from priorities, leadership decisions, team leads, overdue work, and weekly movement.
        </p>
        <ManagementInsights :insights="managementInsights" />
      </section>

      <section>
        <div class="mb-3 flex items-center gap-1.5">
          <h2 class="text-lg font-semibold text-ink-gray-9">Team lead accountability</h2>
          <InfoTooltip
            label="Team lead accountability"
            text="Teams where leadership ownership or delivery accountability needs attention. Use this to know who owns recovery."
          />
        </div>
        <p class="mb-3 text-sm text-ink-gray-6">
          Who owns each domain and whether their team is delivering this week.
          Assign leads on each team’s Overview page.
        </p>
        <LeadAccountabilityPanel :leads="leadAccountability" />
      </section>

      <section>
        <div class="mb-3 flex items-center gap-1.5">
          <h2 class="text-lg font-semibold text-ink-gray-9">Who is not performing?</h2>
          <InfoTooltip
            label="Who is not performing"
            text="People with the heaviest overdue or stale workload. Use it for focused 1:1s, re-prioritization, or workload balancing."
          />
        </div>
        <p class="mb-3 text-sm text-ink-gray-6">
          People with the heaviest overdue load — use in 1:1s and Monday review.
        </p>
        <PeoplePerformancePanel :people="people" />
      </section>

      <section>
        <div class="mb-3 flex items-center gap-1.5">
          <h2 class="text-lg font-semibold text-ink-gray-9">Team health</h2>
          <InfoTooltip
            label="Team health"
            text="Per-team operating health based on overdue tasks, stale work, at-risk goals, sprint slip, and recent completions."
          />
        </div>
        <TeamHealthGrid :teams="teams" />
      </section>

      <section>
        <div class="mb-3 flex items-center gap-1.5">
          <h2 class="text-lg font-semibold text-ink-gray-9">All teams</h2>
          <InfoTooltip
            label="All teams"
            text="Sortable team-level table showing health, lead, overdue work, weekly completions, stale work, at-risk goals, and worst project."
          />
        </div>
        <TeamPerformanceTable :teams="teams" />
      </section>

      <section>
        <div class="mb-3 flex items-center gap-1.5">
          <h2 class="text-lg font-semibold text-ink-gray-9">Initiative watchlist</h2>
          <InfoTooltip
            label="Initiative watchlist"
            text="Open projects that need attention because of at-risk goals, overdue tasks, or stale updates."
          />
        </div>
        <InitiativeWatchlist :initiatives="initiatives" />
      </section>

      <section>
        <div class="mb-3 flex items-center gap-1.5">
          <h2 class="text-lg font-semibold text-ink-gray-9">Escalations</h2>
          <InfoTooltip
            label="Escalations"
            text="Concrete red or amber items to open directly: red teams, at-risk goals, and the most urgent overdue tasks."
          />
        </div>
        <EscalationsList :escalations="escalations" />
      </section>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, watch } from 'vue'
import { Breadcrumbs, Button, FormControl, usePageMeta } from 'frappe-ui'
import dayjs from '@/utils/dayjs'
import ExecutiveSummary from '@/components/executive/ExecutiveSummary.vue'
import ManagementInsights from '@/components/executive/ManagementInsights.vue'
import LeadAccountabilityPanel from '@/components/executive/LeadAccountabilityPanel.vue'
import PeoplePerformancePanel from '@/components/executive/PeoplePerformancePanel.vue'
import TeamHealthGrid from '@/components/executive/TeamHealthGrid.vue'
import TeamPerformanceTable from '@/components/executive/TeamPerformanceTable.vue'
import InitiativeWatchlist from '@/components/executive/InitiativeWatchlist.vue'
import EscalationsList from '@/components/executive/EscalationsList.vue'
import WeeklyMomentum from '@/components/executive/WeeklyMomentum.vue'
import StrategicPriorities from '@/components/executive/StrategicPriorities.vue'
import DecisionQueue from '@/components/executive/DecisionQueue.vue'
import InfoTooltip from '@/components/executive/InfoTooltip.vue'
import {
  executiveCockpit,
  weekStart,
  reloadExecutiveCockpit,
} from '@/data/executive'

function mondayOf(date) {
  const d = dayjs(date)
  return d.subtract(d.day() === 0 ? 6 : d.day() - 1, 'day').format('YYYY-MM-DD')
}

const weekStartInput = computed({
  get() {
    return weekStart.value || executiveCockpit.data?.week?.start || mondayOf(new Date())
  },
  set(v) {
    weekStart.value = v
  },
})

onMounted(() => {
  if (!weekStart.value) {
    weekStart.value = mondayOf(new Date())
  }
  executiveCockpit.fetch()
})

watch(weekStart, () => {
  reloadExecutiveCockpit()
})

function onWeekChange(val) {
  weekStart.value = val ? mondayOf(val) : mondayOf(new Date())
}

function reload() {
  reloadExecutiveCockpit()
}

const teams = computed(() => executiveCockpit.data?.teams || [])
const summary = computed(() => executiveCockpit.data?.summary || {})
const managementInsights = computed(() => executiveCockpit.data?.management_insights || [])
const leadAccountability = computed(() => executiveCockpit.data?.lead_accountability || [])
const people = computed(() => executiveCockpit.data?.people || [])
const initiatives = computed(() => executiveCockpit.data?.initiatives || [])
const escalations = computed(() => executiveCockpit.data?.escalations || [])
const weeklyMomentum = computed(() => executiveCockpit.data?.weekly_momentum || {})
const strategicPriorities = computed(() => executiveCockpit.data?.strategic_priorities || [])
const decisionsRequired = computed(() => executiveCockpit.data?.decisions_required || [])
const links = computed(() => executiveCockpit.data?.links || {})

const weekLabel = computed(() => {
  const w = executiveCockpit.data?.week
  if (!w?.start) return ''
  return w.end ? `${w.start} — ${w.end}` : w.start
})

const generatedAt = computed(() => {
  const t = executiveCockpit.data?.generated_at
  if (!t) return ''
  const parsed = dayjs(t)
  return parsed.isValid() ? parsed.fromNow() : String(t)
})

usePageMeta(() => ({
  title: 'Executive Cockpit',
}))
</script>
