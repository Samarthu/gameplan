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
    @after-leave="newTask = initialData"
  >
    <template #body-content>
      <div class="space-y-4">
        <FormControl label="Title" v-model="newTask.title" autocomplete="off" />
        <FormControl label="Description" type="textarea" v-model="newTask.description" />
        <div class="flex space-x-2">
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
          <Autocomplete
            placeholder="Assign a user"
            :options="assignableUsers"
            v-model="newTask.assigned_to"
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
  status: 'Backlog',
  assigned_to: null,
  project: null,
  team: null,
}

const newTask = ref(initialData)

function statusOptions({ onClick }) {
  return ['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled'].map((status) => {
    return {
      icon: () => h(TaskStatusIcon, { status }),
      label: status,
      onClick: () => onClick(status),
    }
  })
}

const assignableUsers = computed(() => {
  return activeUsers.value.map((user) => ({
    label: user.full_name,
    value: user.name,
  }))
})

let _onSuccess
function show({ defaults, onSuccess } = {}) {
  newTask.value = { ...initialData, ...(defaults || {}) }
  showDialog.value = true
  _onSuccess = onSuccess
}

function onCreateClick(close) {
  let newTaskDoc = {
    ...newTask.value,
    assigned_to: newTask.value.assigned_to?.value || newTask.value.assigned_to,
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

function assigneeValue() {
  return newTask.value.assigned_to?.value || newTask.value.assigned_to
}

function findSimilarTasks() {
  duplicateCandidates.submit({
    title: newTask.value.title,
    assigned_to: assigneeValue(),
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
