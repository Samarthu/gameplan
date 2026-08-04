<template>
  <div>
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 sm:px-5 py-2.5"
    >
      <Breadcrumbs class="h-7" :items="[{ label: 'My Tasks', route: { name: 'MyTasks' } }]" />
      <Button variant="solid" @click="showNewTaskDialog">
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
        Add new
      </Button>
    </header>

    <div class="w-full px-3 sm:px-5">
      <div class="flex flex-wrap items-center justify-between gap-3 pt-3 sm:pt-5">
        <TabButtons
          :buttons="[
            { label: 'All', value: 'all' },
            { label: 'Assigned to me', value: 'assigned' },
            { label: 'Created by me', value: 'owner' },
          ]"
          v-model="currentTab"
        />
        <div class="flex items-center gap-2">
          <TaskSearchInput v-if="taskListRef" v-model="taskListRef.searchQuery" />
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
        </div>
      </div>
      <div class="pb-6 mt-3 sm:mt-4">
        <TaskList
          ref="taskListRef"
          :listOptions="listOptions"
          :groupByStatus="true"
          :viewMode="viewMode"
          @request-new-task="showNewTaskDialog"
        />
        <NewTaskDialog ref="newTaskDialog" />
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { getCachedListResource, usePageMeta, Breadcrumbs, TabButtons, Tooltip } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import { getUser } from '@/data/users'
import LucideListFilter from '~icons/lucide/list-filter'
import LucideX from '~icons/lucide/x'
import TaskSearchInput from '@/components/TaskSearchInput.vue'

let newTaskDialog = ref(null)
let taskListRef = ref(null)
let currentTab = ref('all')
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

let listOptions = computed(() => {
  let me = getUser('sessionUser').name
  let filters = {
    all: { assigned_or_owner: me },
    assigned: { assigned_to: me },
    owner: { owner: me },
  }[currentTab.value]
  return { filters }
})

function showNewTaskDialog(options = {}) {
  newTaskDialog.value.show({
    defaults: {
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

usePageMeta(() => {
  return {
    title: 'My Tasks',
  }
})
</script>
