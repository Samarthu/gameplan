import { computed } from 'vue'
import { createListResource } from 'frappe-ui'

export let sprints = createListResource({
  doctype: 'GP Sprint',
  fields: ['name', 'title', 'team', 'project', 'status', 'start_date', 'end_date'],
  orderBy: 'start_date desc',
  pageLength: 999,
  cache: 'Sprints',
  transform(sprints) {
    return sprints.map((sprint) => {
      sprint.route = {
        name: 'SprintTasks',
        params: {
          teamId: sprint.team,
          sprintId: sprint.name,
        },
      }
      return sprint
    })
  },
  auto: true,
})

export function getTeamSprints(team) {
  return (sprints.data || []).filter((sprint) => sprint.team === team)
}

export function getProjectSprints(project) {
  return (sprints.data || []).filter((sprint) => sprint.project?.toString() === project?.toString())
}

export let getSprint = (sprintId) => {
  if (sprintId == null) return null
  return (sprints.data || []).find((sprint) => sprint.name.toString() === sprintId.toString())
}

export let activeSprints = computed(
  () => (sprints.data || []).filter((sprint) => sprint.status === 'Active'),
)
