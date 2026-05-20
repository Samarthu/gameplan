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
    <template #body-content>
      <div class="space-y-4">
        <FormControl label="Title" v-model="newTask.title" autocomplete="off" />
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
    </template>
  </Dialog>
</template>
<script setup>
import { ref, computed, h } from 'vue'
import { Dialog, FormControl, Autocomplete, Dropdown, TextInput, createResource } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import { activeUsers } from '@/data/users'

const props = defineProps(['modelValue', 'defaults'])
const emit = defineEmits(['update:modelValue'])
const showDialog = ref(false)
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
}

const newTask = ref({ ...initialData })

function resetDialog() {
  newTask.value = { ...initialData }
  assigneeUserIds.value = []
  assigneeAddSelection.value = null
}

function statusOptions({ onClick }) {
  return ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Reopen'].map((status) => {
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
  showDialog.value = true
  _onSuccess = onSuccess
}

function onCreateClick(close) {
  const newTaskDoc = {
    ...newTask.value,
    assignees: assigneeUserIds.value.map((user) => ({ user })),
  }
  createTask
    .submit(newTaskDoc, {
      validate() {
        if (!newTask.value.title) {
          return 'Task title is required'
        }
      },
      onSuccess: _onSuccess,
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
