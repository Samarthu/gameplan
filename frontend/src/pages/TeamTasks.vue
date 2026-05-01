<template>
  <div class="py-6">
    <div class="mb-4.5 flex items-center justify-between">
      <h2 class="text-xl font-semibold text-ink-gray-9">Tasks</h2>
      <Button variant="solid" @click="showNewTaskDialog">
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
        Add new
      </Button>
    </div>
    <TaskList :listOptions="listOptions" :groupByStatus="true" />
    <NewTaskDialog ref="newTaskDialog" />
  </div>
</template>
<script setup>
import { computed, ref } from 'vue'
import { getCachedListResource } from 'frappe-ui'
import { useRoute } from 'vue-router'
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
let newTaskDialog = ref(null)
let listOptions = computed(() => {
  let filters = {
    linked_team: props.team.name,
  }
  if (route.query.linked_project) {
    filters.linked_project = route.query.linked_project
  }
  return { filters }
})

function showNewTaskDialog() {
  newTaskDialog.value.show({
    defaults: {
      team: props.team.name,
      assigned_to: getUser('sessionUser').name,
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
