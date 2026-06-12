import { createResource } from 'frappe-ui'
import { ref } from 'vue'

export const weekStart = ref(null)

export const executiveAccess = createResource({
  url: 'gameplan.executive_dashboard.can_access_executive_dashboard_api',
  cache: 'ExecutiveAccess',
  auto: true,
})

export const executiveCockpit = createResource({
  url: 'gameplan.executive_dashboard.get_ceo_cockpit_data',
  onError(error) {
    console.error('Executive cockpit failed to load', error)
  },
  makeParams() {
    const params = {}
    if (weekStart.value) {
      params.week_start = weekStart.value
    }
    return params
  },
})

export function reloadExecutiveCockpit() {
  return executiveCockpit.reload()
}
