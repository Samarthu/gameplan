import { createResource } from 'frappe-ui'
import { ref } from 'vue'

// Shared filter state for the analytics dashboard.
export const dashboardFilters = ref({
  from_date: null,
  to_date: null,
  team: null,
  project: null,
  people: null,
})

export const dashboardData = createResource({
  url: 'gameplan.dashboard.get_dashboard_data',
  onError(error) {
    console.error('Dashboard failed to load', error)
  },
  makeParams() {
    const f = dashboardFilters.value
    const params = {}
    if (f.from_date) params.from_date = f.from_date
    if (f.to_date) params.to_date = f.to_date
    if (f.team) params.team = f.team
    if (f.project) params.project = f.project
    if (f.people) params.people = f.people
    return params
  },
})

export function reloadDashboard() {
  return dashboardData.reload()
}
