<template>
  <Dialog
    :options="{
      title: 'New Task',
      actions: [
        {
          label: 'Create',
          variant: 'solid',
          onClick: onCreateClick,
        },
      ],
    }"
    :disableOutsideClickToClose="disableOutsideClickToClose"
    v-model="showDialog"
    @after-leave="resetDialog"
  >
    <template #body-main>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">New Task</h3>
          <div class="flex items-center gap-1">
            <Button variant="ghost" @click="minimize">
              <template #icon>
                <LucideMinimize2 class="h-4 w-4 text-ink-gray-9" />
              </template>
            </Button>
            <Button variant="ghost" @click="closeDialog">
              <template #icon>
                <LucideX class="h-4 w-4 text-ink-gray-9" />
              </template>
            </Button>
          </div>
        </div>
        <div class="space-y-4">
        <FormControl label="Title" v-model="newTask.title" autocomplete="off" maxlength="140" />
        <FormControl label="Description" type="textarea" v-model="newTask.description" />
        <div class="flex flex-wrap gap-3">
          <Dropdown
            :options="
              taskTypeOptions({
                onClick: (task_type) => (newTask.task_type = task_type),
              })
            "
          >
            <Button>
              <template #prefix>
                <LucideCircle class="h-4 w-4" />
              </template>
              {{ newTask.task_type }}
            </Button>
          </Dropdown>
          <Dropdown
            :options="
              statusOptions({
                onClick: (status) => (newTask.status = status),
              })
            "
          >
            <Button>
              <template #prefix>
                <TaskStatusIcon :status="newTask.status" />
              </template>
              {{ newTask.status }}
            </Button>
          </Dropdown>
          <TextInput type="date" placeholder="Set due date" v-model="newTask.due_date" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-2">
            <div class="text-sm text-ink-gray-7">Team</div>
            <Autocomplete
              placeholder="Select team"
              :options="teamOptions"
              v-model="selectedTeam"
              @update:modelValue="onTeamPicked"
            />
          </div>
          <div class="space-y-2">
            <div class="text-sm text-ink-gray-7">Project</div>
            <Autocomplete
              placeholder="Select project"
              :options="projectOptions"
              v-model="selectedProject"
              @update:modelValue="onProjectPicked"
            />
          </div>
          <div class="space-y-2">
            <div class="text-sm text-ink-gray-7">Sprint</div>
            <Autocomplete
              placeholder="Select sprint"
              :options="sprintOptions"
              v-model="selectedSprint"
              @update:modelValue="onSprintPicked"
            />
          </div>
        </div>
        <div class="space-y-2">
          <div class="text-sm text-ink-gray-7">Assignees</div>
          <div class="flex flex-wrap gap-1">
            <span
              v-for="uid in assigneeUserIds"
              :key="uid"
              class="inline-flex items-center gap-1 rounded bg-surface-gray-2 px-2 py-0.5 text-sm text-ink-gray-8"
            >
              {{ $user(uid).full_name }}
              <button
                type="button"
                class="leading-none text-ink-gray-5 hover:text-ink-gray-8"
                aria-label="Remove assignee"
                @click="removeAssignee(uid)"
              >
                ×
              </button>
            </span>
          </div>
          <Autocomplete
            placeholder="Add assignee"
            :options="assignableUsersForPicker"
            v-model="assigneeAddSelection"
            @update:modelValue="onAssigneePicked"
          />
        </div>
        <div v-if="newTask.team || newTask.project" class="space-y-2">
          <Button @click="findSimilarTasks" :loading="duplicateCandidates.loading">
            Find similar tasks
          </Button>
          <div v-if="duplicateCandidates.data?.length" class="space-y-1">
            <div
              v-for="task in duplicateCandidates.data"
              :key="task.name"
              class="flex items-center justify-between gap-3 rounded border px-3 py-2"
            >
              <div class="min-w-0">
                <div class="truncate text-base font-medium text-ink-gray-9">{{ task.title }}</div>
                <div class="truncate text-sm text-ink-gray-5">
                  {{ task.team_title || task.team }}
                  <template v-if="task.project_title"> / {{ task.project_title }}</template>
                </div>
              </div>
              <Button
                variant="solid"
                @click="linkExistingTask(task)"
                :loading="linkTaskToTeam.loading"
              >
                Link
              </Button>
            </div>
          </div>
        </div>
        <ErrorMessage class="mt-2" :message="createTask.error" />
        </div>
      </div>
    </template>
  </Dialog>
  <div
    v-if="minimized"
    :style="pillStyle"
    class="fixed z-20 flex w-72 items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3 shadow-xl"
  >
    <button
      class="min-w-0 flex-1 truncate text-left text-sm font-medium text-ink-gray-8"
      @click="expand"
    >
      {{ newTask.title || 'New Task' }}
    </button>
    <div class="flex shrink-0 items-center gap-1">
      <button
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Expand"
        @click="expand"
      >
        <LucideMaximize2 class="h-4 w-4" />
      </button>
      <button
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Close"
        @click="closeFromPill"
      >
        <LucideX class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, h } from 'vue'
import { Dialog, FormControl, Autocomplete, Dropdown, TextInput, createResource } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import { activeUsers } from '@/data/users'
import { activeTeams } from '@/data/teams'
import { getTeamProjects, getProject } from '@/data/projects'
import { getTeamSprints } from '@/data/sprints'
import { nextStackId, pushStack, removeStack, pillStyle as makePillStyle } from '@/utils/minimizedStack'

const props = defineProps(['modelValue', 'defaults'])
const emit = defineEmits(['update:modelValue'])
const showDialog = ref(false)
const minimized = ref(false)
const stackId = nextStackId()
const pillStyle = makePillStyle(stackId)
const assigneeUserIds = ref([])
const assigneeAddSelection = ref(null)

const createTask = createResource({
  url: 'frappe.client.insert',
  makeParams(values) {
    return {
      doc: {
        doctype: 'GP Task',
        ...values,
      },
    }
  },
})
const duplicateCandidates = createResource({
  url: 'gameplan.gameplan.doctype.gp_task.gp_task.get_duplicate_candidates',
})
const linkTaskToTeam = createResource({
  url: 'gameplan.gameplan.doctype.gp_task.gp_task.link_task_to_team',
})
const initialData = {
  title: '',
  description: '',
  task_type: 'Task',
  status: 'Backlog',
  project: null,
  team: null,
  sprint: null,
}

const newTask = ref({ ...initialData })

function resetDialog() {
  // Don't clear the draft when the dialog is only minimized
  if (minimized.value) return
  newTask.value = { ...initialData }
  assigneeUserIds.value = []
  assigneeAddSelection.value = null
}

function minimize() {
  minimized.value = true
  pushStack(stackId)
  showDialog.value = false
}

function expand() {
  minimized.value = false
  removeStack(stackId)
  showDialog.value = true
}

function closeDialog() {
  minimized.value = false
  removeStack(stackId)
  showDialog.value = false
}

function closeFromPill() {
  minimized.value = false
  removeStack(stackId)
  resetDialog()
}

function statusOptions({ onClick }) {
  return ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Reopen', 'Brief Received', 'Ideation', 'Designing', 'Internal Review', 'Stakeholder Review', 'Revisions', 'Finalized', 'Design In Review', 'Design Confirmed', 'Hold', 'QA Accepted', 'Live'].map((status) => {
    return {
      icon: () => h(TaskStatusIcon, { status }),
      label: status,
      onClick: () => onClick(status),
    }
  })
}

function taskTypeOptions({ onClick }) {
  return [
    'Task',
    'Feature',
    'Milestone',
    'Improvement',
    'Bug',
    'Event',
    'Form Response',
    'Meeting Note',
    'Request',
    'Approval',
    'Follow-up',
    'Documentation',
    'Support',
  ].map((task_type) => {
    return {
      label: task_type,
      onClick: () => onClick(task_type),
    }
  })
}

const assignableUsers = computed(() => {
  return activeUsers.value.map((user) => ({
    label: user.full_name,
    value: user.name,
  }))
})

const assignableUsersForPicker = computed(() => {
  const ids = new Set(assigneeUserIds.value)
  return assignableUsers.value.filter((o) => !ids.has(o.value))
})

const teamOptions = computed(() => {
  return activeTeams.value.map((team) => ({
    label: team.title,
    value: team.name,
  }))
})

const selectedTeam = computed(() => {
  if (!newTask.value.team) return null
  return teamOptions.value.find((o) => o.value == newTask.value.team) || null
})

const projectOptions = computed(() => {
  if (!newTask.value.team) return []
  const options = getTeamProjects(newTask.value.team).map((project) => ({
    label: project.title,
    value: project.name.toString(),
  }))
  // Include a pre-selected linked project even if it belongs to another team.
  if (newTask.value.project && !options.find((o) => o.value == newTask.value.project)) {
    const p = getProject(newTask.value.project)
    if (p) options.push({ label: p.title, value: p.name.toString() })
  }
  return options
})

const selectedProject = computed(() => {
  if (!newTask.value.project) return null
  return projectOptions.value.find((o) => o.value == newTask.value.project) || null
})

function onTeamPicked(option) {
  newTask.value.team = option?.value || null
  // Clear project if it no longer belongs to the selected team
  if (!projectOptions.value.find((o) => o.value == newTask.value.project)) {
    newTask.value.project = null
  }
  // Clear sprint if it no longer belongs to the selected team
  if (!sprintOptions.value.find((o) => o.value == newTask.value.sprint)) {
    newTask.value.sprint = null
  }
}

function onProjectPicked(option) {
  newTask.value.project = option?.value || null
}

const sprintOptions = computed(() => {
  if (!newTask.value.team) return []
  return getTeamSprints(newTask.value.team).map((sprint) => ({
    label: sprint.title,
    value: sprint.name.toString(),
  }))
})

const selectedSprint = computed(() => {
  if (!newTask.value.sprint) return null
  return sprintOptions.value.find((o) => o.value == newTask.value.sprint) || null
})

function onSprintPicked(option) {
  newTask.value.sprint = option?.value || null
}

function onAssigneePicked(option) {
  assigneeAddSelection.value = null
  if (!option?.value) return
  if (assigneeUserIds.value.includes(option.value)) return
  assigneeUserIds.value = [...assigneeUserIds.value, option.value]
}

function removeAssignee(uid) {
  assigneeUserIds.value = assigneeUserIds.value.filter((u) => u !== uid)
}

let _onSuccess
function show({ defaults, onSuccess } = {}) {
  const d = { ...(defaults || {}) }
  newTask.value = {
    ...initialData,
    title: d.title ?? initialData.title,
    description: d.description ?? initialData.description,
    task_type: d.task_type ?? initialData.task_type,
    status: d.status ?? initialData.status,
    due_date: d.due_date ?? null,
    project: d.project ?? null,
    team: d.team ?? null,
    sprint: d.sprint ?? null,
  }
  assigneeUserIds.value = []
  if (Array.isArray(d.assignees) && d.assignees.length) {
    assigneeUserIds.value = d.assignees
      .map((x) => (typeof x === 'string' ? x : x.user))
      .filter(Boolean)
  } else if (d.assigned_to) {
    const u = typeof d.assigned_to === 'object' ? d.assigned_to?.value : d.assigned_to
    if (u) assigneeUserIds.value = [u]
  }
  assigneeAddSelection.value = null
  minimized.value = false
  removeStack(stackId)
  showDialog.value = true
  _onSuccess = onSuccess
}

function onCreateClick(close) {
  // Creating under a linked project (owned by another team): the task belongs to
  // the project's own team, and the current team becomes a linked team.
  const project = getProject(newTask.value.project)
  const linkTeam =
    project && newTask.value.team && project.team !== newTask.value.team
      ? newTask.value.team
      : null
  const newTaskDoc = {
    ...newTask.value,
    team: linkTeam ? project.team : newTask.value.team,
    assignees: assigneeUserIds.value.map((user) => ({ user })),
  }
  createTask
    .submit(newTaskDoc, {
      validate() {
        if (!newTask.value.title) {
          return 'Task title is required'
        }
      },
      onSuccess: (doc) => {
        if (linkTeam) {
          // Reload only after the link exists, so the filtered list picks it up.
          linkTaskToTeam.submit(
            { task: doc.name, team: linkTeam, source_project: newTaskDoc.project },
            { onSuccess: () => _onSuccess?.(doc) },
          )
        } else {
          _onSuccess?.(doc)
        }
      },
    })
    .then(close)
}

function findSimilarTasks() {
  duplicateCandidates.submit({
    title: newTask.value.title,
    assignees: assigneeUserIds.value,
    assigned_to: assigneeUserIds.value[0] || null,
    team: newTask.value.team,
    project: newTask.value.project,
  })
}

function linkExistingTask(task) {
  linkTaskToTeam.submit(
    {
      task: task.name,
      team: newTask.value.team,
      source_project: newTask.value.project,
    },
    {
      onSuccess: () => {
        if (_onSuccess) _onSuccess(task)
        showDialog.value = false
      },
    },
  )
}

let disableOutsideClickToClose = computed(() => {
  return createTask.loading || newTask.value?.title != ''
})

defineExpose({ show })
</script>
