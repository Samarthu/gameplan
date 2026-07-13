<template>
  <div class="w-full py-6">
    <div class="mb-4.5 flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-ink-gray-9">Tasks</h2>
      <div class="flex items-center gap-2">
        <TaskSearchInput v-if="taskListRef" v-model="taskListRef.searchQuery" />
        <Tooltip :text="taskListRef?.activeFilterCount ? `${taskListRef.activeFilterCount} active filters` : 'Filters'">
          <button
            type="button"
            class="relative grid h-8 w-8 place-items-center rounded-lg border border-outline-gray-2 bg-surface-white text-ink-gray-6 shadow-sm transition hover:bg-surface-gray-2 hover:text-ink-gray-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            aria-label="Open filters"
            @click.stop="taskListRef?.toggleFiltersPanel($event)"
          >
            <LucideListFilter class="h-4 w-4" />
            <span
              v-if="taskListRef?.activeFilterCount"
              class="absolute -right-1 -top-1 grid h-4 min-w-4 place-items-center rounded-full bg-ink-gray-9 px-1 text-[10px] font-semibold leading-none text-white"
            >
              {{ taskListRef.activeFilterCount }}
            </span>
          </button>
        </Tooltip>
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
import { useRoute, useRouter } from 'vue-router'
import TaskList from '@/components/TaskList.vue'
import TaskSearchInput from '@/components/TaskSearchInput.vue'
import NewTaskDialog from '@/components/NewTaskDialog.vue'
import { getUser } from '@/data/users'
import LucideListFilter from '~icons/lucide/list-filter'

const props = defineProps({
  team: {
    type: Object,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()
let newTaskDialog = ref(null)
let taskListRef = ref(null)
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
let listOptions = computed(() => {
  let filters = {
    linked_team: props.team.name,
  }
  if (route.query.linked_project) {
    filters.linked_project = route.query.linked_project
  }
  return { filters }
})

function showNewTaskDialog(options = {}) {
  newTaskDialog.value.show({
    defaults: {
      team: props.team.name,
      project: route.query.linked_project || null,
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
