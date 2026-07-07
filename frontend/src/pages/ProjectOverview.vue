<template>
  <div class="pt-6">
    <div class="space-y-5 pb-40">
      <ProjectOverviewReadme :project="project" />
      <ProjectOverviewGoals :project="project" />
      <div class="sm:rounded sm:border sm:px-4 sm:py-3">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-ink-gray-8">Discussions</h2>
          <Button :route="{ name: 'ProjectDiscussions' }">View all</Button>
        </div>
        <DiscussionList
          :listOptions="{
            filters: { project: project.doc.name },
            pageLength: 4,
          }"
          :hideLoadMore="true"
        />
      </div>
      <div class="sm:rounded sm:border sm:px-4 sm:py-3">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-ink-gray-8">Sprints</h2>
          <Button @click="showAddSprintDialog = true">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
            Add Sprint
          </Button>
        </div>
        <ul v-if="projectSprints.length" role="list" class="divide-y divide-outline-gray-1">
          <li v-for="sprint in projectSprints" :key="sprint.name">
            <router-link
              :to="{ name: 'SprintTasks', params: { teamId: sprint.team, sprintId: sprint.name } }"
              class="flex items-center justify-between py-2 hover:bg-surface-gray-2 rounded px-1"
            >
              <span class="text-base text-ink-gray-8">{{ sprint.title }}</span>
              <span class="flex items-center gap-3">
                <span class="text-sm text-ink-gray-5">
                  <span v-if="sprint.start_date">{{ $dayjs(sprint.start_date).format('D MMM') }}</span>
                  <span v-if="sprint.start_date && sprint.end_date"> – </span>
                  <span v-if="sprint.end_date">{{ $dayjs(sprint.end_date).format('D MMM') }}</span>
                </span>
                <span
                  class="rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="{
                    'bg-green-100 text-green-700': sprint.status === 'Active',
                    'bg-blue-50 text-blue-600': sprint.status === 'Planned',
                    'bg-surface-gray-3 text-ink-gray-5': sprint.status === 'Completed',
                  }"
                >
                  {{ sprint.status }}
                </span>
              </span>
            </router-link>
          </li>
        </ul>
        <div v-else class="py-4 text-sm text-ink-gray-5">No sprints in this project yet</div>
        <AddSprintDialog
          v-model:show="showAddSprintDialog"
          :team="project.doc.team"
          :project="project.doc.name"
          @success="
            (sprint) => {
              showAddSprintDialog = false
              $router.push({ name: 'SprintTasks', params: { teamId: sprint.team, sprintId: sprint.name } })
            }
          "
        />
      </div>
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div class="sm:rounded sm:border sm:px-4 sm:py-3">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-xl font-semibold text-ink-gray-8">Tasks</h2>
            <Button :route="{ name: 'ProjectTasks' }">View all</Button>
          </div>
          <TaskList
            compact
            :listOptions="{
              filters: {
                project: project.doc.name,
                status: ['in', ['Backlog', 'Todo', 'In Progress', 'Ready for Testing', 'Under Testing', 'Ready to Merge']],
              },
              pageLength: 4,
            }"
          />
        </div>
        <div class="sm:rounded sm:border sm:px-4 sm:py-3">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-xl font-semibold text-ink-gray-8">Documents</h2>
            <Button :route="{ name: 'ProjectPages' }">View all</Button>
          </div>
          <PageList
            :listOptions="{
              filters: {
                project: project.doc.name,
              },
              pageLength: 4,
            }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import ProjectOverviewReadme from './ProjectOverviewReadme.vue'
import ProjectOverviewGoals from './ProjectOverviewGoals.vue'
import AddSprintDialog from '@/components/AddSprintDialog.vue'
import { getProjectSprints } from '@/data/sprints'

export default {
  name: 'ProjectOverview',
  props: ['project'],
  components: {
    ProjectOverviewReadme,
    ProjectOverviewGoals,
    AddSprintDialog,
  },
  data() {
    return {
      showAddSprintDialog: false,
    }
  },
  computed: {
    projectSprints() {
      return getProjectSprints(this.project.doc.name)
    },
  },
}
</script>
