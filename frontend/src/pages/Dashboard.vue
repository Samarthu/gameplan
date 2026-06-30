<template>
  <div>
    <header
      class="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b bg-surface-white px-3 py-2.5 sm:px-5"
    >
      <Breadcrumbs :items="[{ label: 'Dashboard', route: { name: 'Dashboard' } }]" />
      <Button variant="outline" :loading="dashboardData.loading" @click="reloadDashboard">
        Refresh
      </Button>
    </header>

    <!-- Filters -->
    <div class="flex flex-wrap items-end gap-2 border-b bg-surface-white px-3 py-3 sm:px-5">
      <FormControl
        type="select"
        label="Date range"
        class="w-40"
        :options="rangeOptions"
        v-model="rangePreset"
        @update:modelValue="onPresetChange"
      />
      <FormControl
        v-if="rangePreset === 'custom'"
        type="date"
        label="From"
        class="w-40"
        v-model="filters.from_date"
      />
      <FormControl
        v-if="rangePreset === 'custom'"
        type="date"
        label="To"
        class="w-40"
        v-model="filters.to_date"
      />
      <div class="w-52">
        <span class="mb-1.5 block text-xs text-ink-gray-5">Team</span>
        <Autocomplete
          :options="teamOptions"
          :modelValue="filters.team"
          placeholder="All teams"
          @update:modelValue="(o) => (filters.team = o?.value || null)"
        />
      </div>
      <div class="w-52">
        <span class="mb-1.5 block text-xs text-ink-gray-5">Project</span>
        <Autocomplete
          :options="projectOptions"
          :modelValue="filters.project"
          placeholder="All projects"
          @update:modelValue="(o) => (filters.project = o?.value || null)"
        />
      </div>
      <div class="w-52">
        <span class="mb-1.5 block text-xs text-ink-gray-5">People</span>
        <Autocomplete
          :options="peopleOptions"
          :modelValue="filters.people"
          placeholder="All people"
          @update:modelValue="(o) => (filters.people = o?.value || null)"
        />
      </div>
    </div>

    <div
      v-if="dashboardData.loading && !dashboardData.data"
      class="px-5 py-20 text-center text-ink-gray-5"
    >
      Loading dashboard…
    </div>
    <div v-else-if="dashboardData.error" class="px-5 py-20 text-center text-red-700">
      {{ dashboardData.error?.message || 'Failed to load dashboard' }}
      <Button class="mt-4 block mx-auto" variant="outline" @click="reloadDashboard">Retry</Button>
    </div>

    <div v-else class="mx-auto w-full max-w-7xl space-y-6 px-3 py-6 sm:px-5">
      <!-- KPI cards -->
      <div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
        <div v-for="kpi in kpis" :key="kpi.label" class="rounded-lg border bg-surface-white p-4">
          <p class="text-sm text-ink-gray-6">{{ kpi.label }}</p>
          <p class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ kpi.value }}</p>
        </div>
      </div>

      <!-- Assigned tasks list -->
      <details class="group rounded-lg border bg-surface-white">
        <summary class="flex cursor-pointer items-center gap-2 px-4 py-3 [&::-webkit-details-marker]:hidden">
          <svg class="h-4 w-4 shrink-0 text-ink-gray-5 transition-transform group-open:rotate-90" viewBox="0 0 16 16" fill="none">
            <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <div>
            <h2 class="text-base font-semibold text-ink-gray-9">Assigned Tasks</h2>
            <p class="text-sm text-ink-gray-5">All tasks matching the selected filters</p>
          </div>
        </summary>
        <div v-if="taskList.length === 0" class="flex h-32 items-center justify-center border-t text-sm text-ink-gray-5">
          No tasks for the selected filters.
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="border-b bg-surface-gray-1 text-xs text-ink-gray-5">
              <tr>
                <th class="px-4 py-2 text-left font-medium">Title</th>
                <th class="px-4 py-2 text-left font-medium">Status</th>
                <th class="px-4 py-2 text-left font-medium">Type</th>
                <th class="px-4 py-2 text-left font-medium">Team</th>
                <th class="px-4 py-2 text-left font-medium">Project</th>
                <th class="px-4 py-2 text-left font-medium">Assigned To</th>
                <th class="px-4 py-2 text-left font-medium">Due Date</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr
                v-for="task in taskList"
                :key="task.name"
                class="hover:bg-surface-gray-1"
              >
                <td class="max-w-xs truncate px-4 py-2 text-ink-gray-9">
                  <a
                    :href="`/g/task/${task.name}`"
                    class="hover:text-ink-blue-3 hover:underline"
                  >{{ task.title || task.name }}</a>
                </td>
                <td class="px-4 py-2">
                  <span
                    class="inline-block rounded px-1.5 py-0.5 text-xs font-medium"
                    :class="statusClass(task.status)"
                  >{{ task.status }}</span>
                </td>
                <td class="px-4 py-2 text-ink-gray-6">{{ task.task_type || '—' }}</td>
                <td class="px-4 py-2 text-ink-gray-6">{{ task.team_title || '—' }}</td>
                <td class="px-4 py-2 text-ink-gray-6">{{ task.project_title || '—' }}</td>
                <td class="px-4 py-2">
                  <div v-if="task.assignees && task.assignees.length" class="flex items-center">
                    <div
                      v-for="a in task.assignees"
                      :key="a.user"
                      class="-ml-1.5 h-6 w-6 shrink-0 overflow-hidden rounded-full bg-blue-500 ring-2 ring-white first:ml-0"
                      :title="a.name"
                    >
                      <img
                        v-if="a.image"
                        :src="a.image"
                        :alt="a.name"
                        class="h-full w-full object-cover"
                      />
                      <span
                        v-else
                        class="flex h-full w-full items-center justify-center text-xs font-medium text-white"
                      >{{ (a.name || '?')[0].toUpperCase() }}</span>
                    </div>
                  </div>
                  <span v-else class="text-ink-gray-4">—</span>
                </td>
                <td class="px-4 py-2" :class="task.due_date && isPast(task.due_date) ? 'text-red-600' : 'text-ink-gray-6'">
                  {{ task.due_date || '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>

      <!-- Charts -->
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Task activity" subtitle="Created vs completed over time">
          <FrappeChart v-if="hasData(activity)" type="line" :data="activity" :height="260" />
          <Empty v-else />
        </ChartCard>

        <ChartCard title="Tasks by status">
          <FrappeChart v-if="hasData(byStatus)" type="donut" :data="byStatus" :height="260" />
          <Empty v-else />
        </ChartCard>

        <ChartCard title="Tasks by team">
          <FrappeChart v-if="hasData(byTeam)" type="bar" :data="byTeam" :height="260" />
          <Empty v-else />
        </ChartCard>

        <ChartCard title="Tasks by type">
          <FrappeChart v-if="hasData(byType)" type="bar" :data="byType" :height="260" />
          <Empty v-else />
        </ChartCard>

        <ChartCard title="Tasks by sprint" class="lg:col-span-2">
          <FrappeChart v-if="hasData(bySprint)" type="bar" :data="bySprint" :height="260" />
          <Empty v-else />
        </ChartCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, h, onMounted, ref, watch } from 'vue'
import { Autocomplete, Breadcrumbs, Button, FormControl, usePageMeta } from 'frappe-ui'
import dayjs from '@/utils/dayjs'
import FrappeChart from '@/components/charts/FrappeChart.vue'
import { dashboardData, dashboardFilters, reloadDashboard } from '@/data/dashboard'

const filters = dashboardFilters

const rangeOptions = [
  { label: 'Last 7 Days', value: '7' },
  { label: 'Last 30 Days', value: '30' },
  { label: 'Last 90 Days', value: '90' },
  { label: 'Custom', value: 'custom' },
]
const rangePreset = ref('7')

function applyPreset(days) {
  filters.value.to_date = dayjs().format('YYYY-MM-DD')
  filters.value.from_date = dayjs().subtract(days - 1, 'day').format('YYYY-MM-DD')
}

function onPresetChange(val) {
  if (val !== 'custom') applyPreset(Number(val))
}

// Filter options are computed server-side from the in-scope task set (within
// your reporting tree) so the counts reconcile and the lists cascade. Private
// teams/projects are surfaced too, marked distinctly.
function withPrivacy(opt) {
  return { value: opt.value, label: opt.is_private ? `${opt.label} · private` : opt.label }
}
const teamOptions = computed(() => (dashboardData.data?.team_options || []).map(withPrivacy))
const projectOptions = computed(() =>
  (dashboardData.data?.project_options || []).map(withPrivacy),
)
const peopleOptions = computed(() => dashboardData.data?.people_options || [])

// Cascade: changing a parent filter clears now-irrelevant child selections.
// (Option lists arrive with the next data load, so we reset rather than diff.)
watch(
  () => filters.value.team,
  () => {
    filters.value.project = null
    filters.value.people = null
  },
)
watch(
  () => filters.value.project,
  () => {
    filters.value.people = null
  },
)

// Chart data
const summary = computed(() => dashboardData.data?.summary || {})
const activity = computed(() => dashboardData.data?.activity || { labels: [], datasets: [] })
const byStatus = computed(() => dashboardData.data?.by_status || { labels: [], datasets: [] })
const byTeam = computed(() => dashboardData.data?.by_team || { labels: [], datasets: [] })
const byType = computed(() => dashboardData.data?.by_type || { labels: [], datasets: [] })
const bySprint = computed(() => dashboardData.data?.by_sprint || { labels: [], datasets: [] })

const kpis = computed(() => [
  { label: 'Tasks', value: summary.value.total_tasks ?? 0 },
  { label: 'Completion Rate', value: `${summary.value.completion_rate ?? 0}%` },
  { label: 'Open Tasks', value: summary.value.open_tasks ?? 0 },
  { label: 'Overdue Tasks', value: summary.value.overdue_tasks ?? 0 },
  { label: 'Avg. Resolution', value: `${summary.value.avg_resolution_days ?? 0} days` },
])

const taskList = computed(() => dashboardData.data?.task_list || [])

const STATUS_CLASSES = {
  Done: 'bg-green-100 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
  'In Progress': 'bg-blue-100 text-blue-700',
  'Under Testing': 'bg-yellow-100 text-yellow-700',
  'Ready to Merge': 'bg-purple-100 text-purple-700',
  Backlog: 'bg-gray-100 text-gray-600',
  Todo: 'bg-gray-100 text-gray-600',
  Reopen: 'bg-orange-100 text-orange-600',
}
function statusClass(status) {
  return STATUS_CLASSES[status] || 'bg-gray-100 text-gray-600'
}
function isPast(date) {
  return date && date < dayjs().format('YYYY-MM-DD')
}

function hasData(chart) {
  const values = chart?.datasets?.[0]?.values || []
  return chart?.labels?.length && values.some((v) => v > 0)
}

// Small presentational helpers (kept inline to avoid extra files)
const ChartCard = (props, { slots }) =>
  h('div', { class: 'rounded-lg border bg-surface-white p-4' }, [
    h('h2', { class: 'text-base font-semibold text-ink-gray-9' }, props.title),
    props.subtitle
      ? h('p', { class: 'mt-0.5 text-sm text-ink-gray-5' }, props.subtitle)
      : null,
    h('div', { class: 'mt-2' }, slots.default?.()),
  ])
ChartCard.props = ['title', 'subtitle']

const Empty = () =>
  h(
    'div',
    { class: 'flex h-[260px] items-center justify-center text-sm text-ink-gray-5' },
    'No data for the selected filters.',
  )

let debounce = null
watch(
  filters,
  () => {
    clearTimeout(debounce)
    debounce = setTimeout(() => reloadDashboard(), 250)
  },
  { deep: true },
)

onMounted(() => {
  if (!filters.value.from_date) applyPreset(7)
  dashboardData.fetch()
})

usePageMeta(() => ({ title: 'Dashboard' }))
</script>
