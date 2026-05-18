<template>
  <div class="w-full px-5 py-6">
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
import { getUser } from '@/data/users'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  project: {
    type: Object,
    required: true,
  },
})

let newTaskDialog = ref(null)
const route = useRoute()
const router = useRouter()
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
