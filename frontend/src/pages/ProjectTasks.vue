<template>
  <div class="w-full px-5 py-6">
    <div class="mb-4.5 flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-ink-gray-9">Tasks</h2>
      <div class="flex items-center gap-2">
        <TaskSearchInput v-if="taskListRef" v-model="taskListRef.searchQuery" />
        <button
          v-if="taskListRef"
          type="button"
          class="h-8 rounded-lg border px-2.5 text-sm font-medium shadow-sm transition"
          :class="taskListRef.assignedToMeActive ? 'border-gray-900 bg-gray-900 text-white' : 'border-outline-gray-2 bg-surface-white text-ink-gray-7 hover:bg-surface-gray-2'"
          @click="taskListRef.toggleAssignedToMe()"
        >
          Assigned to me
        </button>
        <div class="relative">
          <Tooltip :text="taskListRef?.activeFilterCount ? taskListRef.activeFilterLabels.join(', ') : 'Filters'">
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
            { label: 'Team', value: 'team' },
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
  </div>
</template>
<script setup>
import { computed, ref } from 'vue'
import { getCachedListResource, TabButtons, Tooltip } from 'frappe-ui'
import { getUser } from '@/data/users'
import { useRoute, useRouter } from 'vue-router'
import LucideListFilter from '~icons/lucide/list-filter'
import LucideX from '~icons/lucide/x'
import TaskSearchInput from '@/components/TaskSearchInput.vue'

const props = defineProps({
  project: {
    type: Object,
    required: true,
  },
})

let newTaskDialog = ref(null)
let taskListRef = ref(null)
const route = useRoute()
const router = useRouter()
let viewMode = computed({
  get() {
    return ['kanban', 'team'].includes(route.query.view) ? route.query.view : 'list'
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
    project: props.project.name,
  },
}))

function showNewTaskDialog(options = {}) {
  newTaskDialog.value.show({
    defaults: {
      project: props.project.name,
      team: props.project.doc.team,
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
