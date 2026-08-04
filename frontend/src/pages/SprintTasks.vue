<template>
  <div class="w-full px-5 py-6">
    <div class="mb-4.5 flex flex-wrap items-center justify-between gap-3">
      <div>
        <div class="flex items-center gap-2">
          <router-link
            v-if="sprintProject"
            :to="{ name: 'ProjectOverview', params: { teamId: props.teamId, projectId: sprintProject.name } }"
            class="text-xl font-semibold text-ink-gray-5 hover:text-ink-gray-8"
          >
            {{ sprintProject.title }} <span class="text-ink-gray-4">/</span>
          </router-link>
          <h2 class="text-xl font-semibold text-ink-gray-9">{{ sprint?.title }}</h2>
          <span
            v-if="sprint?.status"
            class="rounded-full px-2 py-0.5 text-xs font-medium"
            :class="statusClass"
          >
            {{ sprint?.status }}
          </span>
          <Button v-if="sprint" variant="ghost" @click="openEditSprint" aria-label="Edit sprint">
            <template #icon>
              <LucidePencil class="h-4 w-4 text-ink-gray-6" />
            </template>
          </Button>
        </div>
        <p v-if="sprint?.start_date || sprint?.end_date" class="mt-1 text-sm text-ink-gray-5">
          <span v-if="sprint?.start_date">{{ formatDate(sprint.start_date) }}</span>
          <span v-if="sprint?.start_date && sprint?.end_date"> – </span>
          <span v-if="sprint?.end_date">{{ formatDate(sprint.end_date) }}</span>
        </p>
      </div>
      <div class="flex items-center gap-2">
        <TaskSearchInput v-if="taskListRef" v-model="taskListRef.searchQuery" />
        <div class="relative">
          <Tooltip
            :text="taskListRef?.activeFilterCount ? taskListRef.activeFilterLabels.join(', ') : 'Filters'"
          >
            <button
              type="button"
              class="relative grid h-8 w-8 place-items-center rounded-lg border border-outline-gray-2 bg-surface-white text-ink-gray-6 shadow-sm transition hover:bg-surface-gray-2 hover:text-ink-gray-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
              aria-label="Open filters"
              @click.stop="taskListRef?.toggleFiltersPanel($event)"
            >
              <LucideListFilter class="h-4 w-4" />
            </button>
          </Tooltip>
          <span
            v-if="taskListRef?.activeFilterCount"
            class="pointer-events-none absolute -left-1.5 -top-1.5 z-10 grid h-4 min-w-4 place-items-center rounded-full bg-gray-900 px-1 text-[10px] font-semibold leading-none text-white"
          >
            {{ taskListRef.activeFilterCount }}
          </span>
          <Tooltip v-if="taskListRef?.activeFilterCount" text="Clear filters">
            <button
              type="button"
              class="absolute -right-1.5 -top-1.5 grid h-4 w-4 place-items-center rounded-full border border-outline-gray-2 bg-surface-white text-ink-gray-6 shadow-sm hover:bg-surface-red-1 hover:text-red-500"
              aria-label="Clear filters"
              @click.stop="taskListRef?.clearAllFilters()"
            >
              <LucideX class="h-3 w-3" />
            </button>
          </Tooltip>
        </div>
        <TabButtons
          :buttons="[
            { label: 'List', value: 'list' },
            { label: 'Kanban', value: 'kanban' },
          ]"
          v-model="viewMode"
        />
        <Button variant="solid" @click="showNewTaskDialog">
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
          Add new
        </Button>
      </div>
    </div>
    <TaskList
      ref="taskListRef"
      :listOptions="listOptions"
      :groupByStatus="true"
      :viewMode="viewMode"
      @request-new-task="showNewTaskDialog"
    />
    <NewTaskDialog ref="newTaskDialog" />
    <Dialog
      v-model="showEditDialog"
      :options="{
        title: 'Edit Sprint',
        actions: [
          { label: 'Save', variant: 'solid', onClick: saveSprint },
          { label: 'Delete', theme: 'red', onClick: openConfirmDelete },
        ],
      }"
    >
      <template #body-content>
        <div class="space-y-4">
          <FormControl label="Name" v-model="editForm.title" autocomplete="off" />
          <FormControl
            label="Status"
            type="select"
            :options="['Planned', 'Active', 'Completed']"
            v-model="editForm.status"
          />
          <div class="grid grid-cols-2 gap-3">
            <FormControl label="From date" type="date" v-model="editForm.start_date" />
            <FormControl label="To date" type="date" v-model="editForm.end_date" />
          </div>
          <ErrorMessage :message="editError" />
        </div>
      </template>
    </Dialog>
    <Dialog
      v-model="showConfirmDelete"
      :options="{
        title: 'Delete Sprint',
        actions: [
          { label: 'Delete', variant: 'solid', theme: 'red', loading: sprints.delete.loading, onClick: deleteSprint },
          { label: 'Cancel', onClick: (close) => close() },
        ],
      }"
    >
      <template #body-content>
        <p class="text-base text-ink-gray-7">Delete this sprint? This cannot be undone.</p>
        <ErrorMessage class="mt-2" :message="deleteError" />
      </template>
    </Dialog>
  </div>
</template>
<script setup>
import { computed, ref } from 'vue'
import { getCachedListResource, TabButtons, Tooltip, Dialog, FormControl, ErrorMessage, call } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import TaskList from '@/components/TaskList.vue'
import TaskSearchInput from '@/components/TaskSearchInput.vue'
import NewTaskDialog from '@/components/NewTaskDialog.vue'
import { sprints, getSprint } from '@/data/sprints'
import { getProject } from '@/data/projects'
import { getUser } from '@/data/users'
import LucideListFilter from '~icons/lucide/list-filter'
import LucideX from '~icons/lucide/x'
import LucidePencil from '~icons/lucide/pencil'

const props = defineProps({
  sprintId: {
    type: String,
    required: true,
  },
  teamId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()
let newTaskDialog = ref(null)
let taskListRef = ref(null)

let sprint = computed(() => getSprint(props.sprintId))
let sprintProject = computed(() => (sprint.value?.project ? getProject(sprint.value.project) : null))

let viewMode = computed({
  get() {
    return route.query.view === 'kanban' ? 'kanban' : 'list'
  },
  set(value) {
    let query = { ...route.query }
    if (value !== 'list') {
      query.view = value
    } else {
      delete query.view
    }
    router.replace({ query })
  },
})

let listOptions = computed(() => ({
  filters: {
    sprint: props.sprintId,
  },
}))

let statusClass = computed(() => {
  const s = sprint.value?.status
  if (s === 'Active') return 'bg-green-100 text-green-700'
  if (s === 'Completed') return 'bg-surface-gray-3 text-ink-gray-6'
  return 'bg-blue-50 text-blue-600'
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

const showEditDialog = ref(false)
const showConfirmDelete = ref(false)
const editError = ref(null)
const deleteError = ref(null)

async function openConfirmDelete() {
  editError.value = null
  const count = await call('frappe.client.get_count', {
    doctype: 'GP Task',
    filters: { sprint: props.sprintId },
  })
  if (count) {
    editError.value = `Delete the ${count} task(s) in this sprint before deleting it.`
    return
  }
  deleteError.value = null
  showConfirmDelete.value = true
}
const editForm = ref({ title: '', status: 'Planned', start_date: null, end_date: null })

function openEditSprint() {
  const s = sprint.value
  if (!s) return
  editForm.value = {
    title: s.title || '',
    status: s.status || 'Planned',
    start_date: s.start_date || null,
    end_date: s.end_date || null,
  }
  editError.value = null
  showEditDialog.value = true
}

function saveSprint(close) {
  if (!editForm.value.title) {
    editError.value = 'Name is required'
    return
  }
  if (
    editForm.value.start_date &&
    editForm.value.end_date &&
    editForm.value.end_date < editForm.value.start_date
  ) {
    editError.value = 'To date cannot be before from date'
    return
  }
  sprints.setValue.submit(
    { name: props.sprintId, ...editForm.value },
    {
      onSuccess: () => {
        sprints.reload()
        close()
      },
      onError: (e) => (editError.value = e.messages?.[0] || 'Failed to save'),
    },
  )
}

function deleteSprint(close) {
  deleteError.value = null
  sprints.delete.submit(props.sprintId, {
    onSuccess: () => {
      sprints.reload()
      close()
      showEditDialog.value = false
      router.push({ name: 'TeamOverview', params: { teamId: props.teamId } })
    },
    onError: (e) => {
      // Keep the confirm dialog open so the reason is visible.
      deleteError.value = e.messages?.[0] || 'Delete all tasks in this sprint before deleting it.'
    },
  })
}

function showNewTaskDialog(options = {}) {
  newTaskDialog.value.show({
    defaults: {
      team: props.teamId,
      sprint: props.sprintId,
      project: sprint.value?.project || null,
      assigned_to: getUser('sessionUser').name,
      ...options,
    },
    onSuccess: () => {
      let tasks = getCachedListResource(['Tasks', listOptions.value])
      if (tasks) {
        tasks.reload()
      }
    },
  })
}
</script>
