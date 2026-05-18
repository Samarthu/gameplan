<template>
  <div class="w-full py-6">
    <div class="mb-4.5 flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-ink-gray-9">Tasks</h2>
      <div class="flex items-center gap-2">
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
import { getCachedListResource, TabButtons } from 'frappe-ui'
import { useRoute, useRouter } from 'vue-router'
import TaskList from '@/components/TaskList.vue'
import NewTaskDialog from '@/components/NewTaskDialog.vue'
import { getUser } from '@/data/users'

const props = defineProps({
  team: {
    type: Object,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()
let newTaskDialog = ref(null)
let viewMode = computed({
  get() {
    return route.query.view === 'kanban' ? 'kanban' : 'list'
  },
  set(value) {
    let query = { ...route.query }
    if (value === 'kanban') {
      query.view = 'kanban'
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
      assigned_to: getUser('sessionUser').name,
      status: options.status,
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
