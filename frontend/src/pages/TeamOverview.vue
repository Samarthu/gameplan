<template>
  <div class="mt-6">
    <ReadmeEditor
      :resource="team"
      fieldname="readme"
      :border="true"
      :collapsible="true"
      :editable="!team.doc.archived_at"
    />

    <div class="mt-8">
      <div class="mb-5 flex items-center justify-between space-x-2">
        <h2 class="text-2xl font-semibold text-ink-gray-9">Projects</h2>
        <div class="flex items-stretch space-x-2">
          <TabButtons :buttons="[{ label: 'Active' }, { label: 'Archived' }]" v-model="activeTab" />
          <Button :route="{ name: 'TeamTasks' }"> Tasks </Button>
          <Button v-if="teamProjects.length" @click="createNewProjectDialog = true" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
            Add Project
          </Button>
        </div>
      </div>
      <ul role="list" class="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <li v-for="project in projectsList" :key="project.name" class="flow-root">
          <div
            class="group relative items-center rounded-lg p-3 shadow transition-colors focus-within:ring focus-within:ring-outline-gray-2 hover:bg-surface-gray-2"
          >
            <div>
              <h3 class="overflow-hidden text-lg font-medium text-ink-gray-9">
                <router-link
                  :to="projectRoute(project)"
                  class="inline-flex w-full overflow-hidden text-ellipsis whitespace-nowrap focus:outline-none"
                >
                  <span class="absolute inset-0" aria-hidden="true" />
                  <span class="inline-flex items-center">
                    {{ project.title }}
                    <LucideLock v-if="project.is_private" class="ml-1 h-3 w-3" />
                    <span
                      v-if="project.is_linked_project"
                      class="ml-1 rounded bg-surface-gray-2 px-1.5 py-0.5 text-xs font-normal text-ink-gray-6"
                    >
                      Linked
                    </span>
                  </span>
                </router-link>
              </h3>
              <p class="mt-1 text-base">
                <template v-if="project.tasks_count">
                  <span class="text-ink-gray-9">
                    {{ project.tasks_count }}
                  </span>
                  <span class="text-ink-gray-7"
                    >&nbsp;{{ project.tasks_count === 1 ? 'task' : 'tasks' }}
                  </span>
                  &middot;
                </template>
                <template v-if="project.discussions_count">
                  <span class="text-ink-gray-9">
                    {{ project.discussions_count }}
                  </span>
                  <span class="text-ink-gray-7"
                    >&nbsp;{{ project.discussions_count === 1 ? 'discussion' : 'discussions' }}
                  </span>
                </template>
                <span
                  class="text-ink-gray-7"
                  v-if="project.tasks_count + project.discussions_count == 0"
                >
                  {{ $dayjs(project.creation).fromNow() }}
                </span>
              </p>
            </div>
          </div>
        </li>
        <button
          v-if="teamProjects.length === 0"
          class="group relative flex items-center space-x-4 rounded-xl border border-gray-100 p-2 text-left transition-colors focus-within:ring-2 focus-within:ring-blue-500 hover:bg-surface-gray-2"
          @click="createNewProjectDialog = true"
        >
          <div
            class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-surface-gray-2 transition-colors group-hover:bg-surface-white"
          >
            <LucidePlus class="w-5 text-ink-gray-5" />
          </div>
          <div>
            <h3 class="text-lg font-medium text-ink-gray-9">Add Project</h3>
          </div>
        </button>
      </ul>
      <Dialog :options="{ title: 'Create project' }" v-model="createNewProjectDialog">
        <template #body-main>
          <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
            <div class="mb-6 flex items-center justify-between">
              <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">Create project</h3>
              <div class="flex items-center gap-1">
                <Button variant="ghost" @click="minimizeProject">
                  <template #icon>
                    <LucideMinimize2 class="h-4 w-4 text-ink-gray-9" />
                  </template>
                </Button>
                <Button variant="ghost" @click="closeProject">
                  <template #icon>
                    <LucideX class="h-4 w-4 text-ink-gray-9" />
                  </template>
                </Button>
              </div>
            </div>
            <div class="space-y-5">
              <FormControl label="Title" v-model="newProject.title" @keydown.enter="createProject" />
              <FormControl
                v-if="!team.doc.is_private"
                type="select"
                label="Visibility"
                :options="[
                  { label: 'Visible to everyone', value: 0 },
                  { label: 'Visible to team members (Private)', value: 1 },
                ]"
                v-model="newProject.is_private"
              />
              <ErrorMessage :message="projects.insert.error" />
            </div>
          </div>
        </template>
        <template #actions>
          <Button
            size="md"
            class="w-full"
            variant="solid"
            @click="createProject"
            :loading="projects.insert.loading"
          >
            Create
          </Button>
        </template>
      </Dialog>
      <div
        v-if="projectMinimized"
        class="fixed bottom-4 right-4 z-20 flex w-72 items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3 shadow-xl"
      >
        <button
          class="min-w-0 flex-1 truncate text-left text-sm font-medium text-ink-gray-8"
          @click="expandProject"
        >
          {{ newProject.title || 'Create project' }}
        </button>
        <div class="flex shrink-0 items-center gap-1">
          <button
            class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
            aria-label="Expand"
            @click="expandProject"
          >
            <LucideMaximize2 class="h-4 w-4" />
          </button>
          <button
            class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
            aria-label="Close"
            @click="closeProjectFromPill"
          >
            <LucideX class="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Sprints Section -->
    <div class="mt-10">
      <div class="mb-5 flex items-center justify-between space-x-2">
        <h2 class="text-2xl font-semibold text-ink-gray-9">Sprints</h2>
        <div class="flex items-stretch space-x-2">
          <TabButtons
            :buttons="[{ label: 'All' }, { label: 'Planned' }, { label: 'Active' }, { label: 'Completed' }]"
            v-model="sprintTab"
          />
          <Button @click="showAddSprintDialog = true" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
            Add Sprint
          </Button>
        </div>
      </div>
      <ul v-if="filteredSprints.length" role="list" class="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <li v-for="sprint in filteredSprints" :key="sprint.name" class="flow-root">
          <router-link
            :to="{ name: 'SprintTasks', params: { teamId: team.name, sprintId: sprint.name } }"
            class="group relative flex flex-col rounded-lg p-3 shadow transition-colors hover:bg-surface-gray-2 focus:outline-none focus-within:ring focus-within:ring-outline-gray-2"
          >
            <div class="flex items-center justify-between">
              <h3 class="overflow-hidden text-ellipsis whitespace-nowrap text-lg font-medium text-ink-gray-9">
                {{ sprint.title }}
              </h3>
              <span
                class="ml-2 shrink-0 rounded-full px-2 py-0.5 text-xs font-medium"
                :class="{
                  'bg-green-100 text-green-700': sprint.status === 'Active',
                  'bg-blue-50 text-blue-600': sprint.status === 'Planned',
                  'bg-surface-gray-3 text-ink-gray-5': sprint.status === 'Completed',
                }"
              >
                {{ sprint.status }}
              </span>
            </div>
            <p class="mt-1 text-base">
              <template v-if="sprint.tasks_count">
                <span class="text-ink-gray-9">{{ sprint.tasks_count }}</span>
                <span class="text-ink-gray-7">&nbsp;{{ sprint.tasks_count === 1 ? 'task' : 'tasks' }}</span>
                <span class="text-ink-gray-5" v-if="sprint.start_date || sprint.end_date"> &middot; </span>
              </template>
              <span class="text-ink-gray-5">
                <span v-if="sprint.start_date">{{ formatDate(sprint.start_date) }}</span>
                <span v-if="sprint.start_date && sprint.end_date"> – </span>
                <span v-if="sprint.end_date">{{ formatDate(sprint.end_date) }}</span>
                <span v-if="!sprint.tasks_count && !sprint.start_date && !sprint.end_date">No dates set</span>
              </span>
            </p>
          </router-link>
        </li>
      </ul>
      <div
        v-else-if="teamSprints.length && !filteredSprints.length"
        class="py-4 text-sm text-ink-gray-5"
      >
        No {{ sprintTab.toLowerCase() }} sprints
      </div>
      <button
        v-if="!teamSprints.length"
        class="group relative flex items-center space-x-4 rounded-xl border border-gray-100 p-2 text-left transition-colors focus-within:ring-2 focus-within:ring-blue-500 hover:bg-surface-gray-2"
        @click="showAddSprintDialog = true"
      >
        <div
          class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-surface-gray-2 transition-colors group-hover:bg-surface-white"
        >
          <LucidePlus class="w-5 text-ink-gray-5" />
        </div>
        <div>
          <h3 class="text-lg font-medium text-ink-gray-9">Add Sprint</h3>
        </div>
      </button>
      <AddSprintDialog
        :show="showAddSprintDialog"
        :team="team.name"
        @update:show="(v) => { showAddSprintDialog = v }"
        @success="
          (sprint) => {
            showAddSprintDialog = false
            $router.push({ name: 'SprintTasks', params: { teamId: team.name, sprintId: sprint.name } })
          }
        "
      />
    </div>
  </div>
</template>
<script>
import { Dialog, FormControl, TextInput, TabButtons } from 'frappe-ui'
import { projects, getTeamProjects, getTeamArchivedProjects } from '@/data/projects'
import { getTeamSprints } from '@/data/sprints'
import AddSprintDialog from '@/components/AddSprintDialog.vue'

export default {
  name: 'TeamOverview',
  props: ['team'],
  components: {
    Dialog,
    TabButtons,
    TextInput,
    FormControl,
    AddSprintDialog,
  },
  data() {
    return {
      createNewProjectDialog: false,
      projectMinimized: false,
      newProject: { title: '', is_private: 0 },
      activeTab: 'Active',
      showAddSprintDialog: false,
      sprintTab: 'All',
    }
  },
  resources: {
    linkedProjects() {
      return {
        url: 'gameplan.gameplan.doctype.gp_task.gp_task.get_linked_projects',
        params: { team: this.team.name },
        auto: true,
      }
    },
    sprintTaskCounts() {
      return {
        url: 'gameplan.gameplan.doctype.gp_sprint.gp_sprint.get_sprint_task_counts',
        params: { team: this.team.name },
        auto: true,
      }
    },
  },
  watch: {
    'team.name'() {
      this.$resources.linkedProjects.fetch({ team: this.team.name })
      this.$resources.sprintTaskCounts.fetch({ team: this.team.name })
    },
  },
  computed: {
    projects() {
      return projects
    },
    projectsList() {
      return this.activeTab === 'Active' ? this.activeProjects : this.archivedProjects
    },
    activeProjects() {
      return [
        ...this.teamProjects.filter((project) => !project.archived_at),
        ...this.linkedProjectCards,
      ]
    },
    archivedProjects() {
      return getTeamArchivedProjects(this.team.name)
    },
    teamProjects() {
      return getTeamProjects(this.team.name)
    },
    filteredSprints() {
      if (this.sprintTab === 'All') return this.teamSprints
      return this.teamSprints.filter((s) => s.status === this.sprintTab)
    },
    teamSprints() {
      const counts = this.$resources.sprintTaskCounts.data || {}
      return getTeamSprints(this.team.name).map((sprint) => ({
        ...sprint,
        tasks_count: counts[sprint.name] || 0,
      }))
    },
    linkedProjectCards() {
      return (this.$resources.linkedProjects.data || []).map((project) => ({
        ...project,
        name: String(project.name),
        tasks_count: Number(project.tasks_count || 0),
        discussions_count: 0,
      }))
    },
  },
  methods: {
    projectRoute(project) {
      if (project.is_linked_project) {
        return {
          name: 'TeamTasks',
          params: { teamId: this.team.name },
          query: { linked_project: project.name },
        }
      }
      return {
        name: 'Project',
        params: { teamId: this.team.name, projectId: project.name },
      }
    },
    formatDate(dateStr) {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    },
    createProject() {
      projects.insert.submit(
        {
          team: this.team.name,
          ...this.newProject,
        },
        {
          onSuccess: (project) => {
            projects.reload()
            this.newProject = this.$options.data().newProject
            this.projectMinimized = false
            this.createNewProjectDialog = false
            this.$router.push({
              name: 'Project',
              params: { projectId: project.name },
            })
          },
        },
      )
    },
    minimizeProject() {
      this.projectMinimized = true
      this.createNewProjectDialog = false
    },
    expandProject() {
      this.projectMinimized = false
      this.createNewProjectDialog = true
    },
    closeProject() {
      this.projectMinimized = false
      this.createNewProjectDialog = false
    },
    closeProjectFromPill() {
      this.projectMinimized = false
      this.newProject = this.$options.data().newProject
    },
  },
}
</script>
