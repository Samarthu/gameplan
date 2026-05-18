<template>
  <div>
    <div v-if="tasksResource.data?.length" class="overflow-x-auto pb-3">
      <div class="flex min-h-[calc(100vh-13rem)] gap-3">
        <section
          v-for="group in kanbanGroups"
          :key="group.title"
          class="flex w-72 shrink-0 flex-col rounded-lg border border-outline-gray-2 bg-surface-gray-1/70"
          :class="[
            kanbanColumnClass(group.title),
            dragOverStatus === group.title ? 'ring-2 ring-outline-gray-4' : '',
          ]"
          @dragover.prevent="onColumnDragOver(group.title)"
          @dragleave="onColumnDragLeave(group.title, $event)"
          @drop.prevent="onDrop(group.title)"
        >
          <div class="flex items-center justify-between gap-2 px-3 py-3">
            <div class="flex min-w-0 items-center gap-2">
              <TaskStatusIcon :status="group.title" />
              <span class="truncate text-sm font-semibold uppercase text-ink-gray-8">{{ group.title }}</span>
              <span class="text-sm font-semibold text-ink-gray-5">{{ group.tasks.length }}</span>
            </div>
            <button
              class="grid h-6 w-6 shrink-0 place-items-center rounded text-ink-gray-5 hover:bg-surface-gray-3 hover:text-ink-gray-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
              @click="$emit('request-new-task', { status: group.title })"
            >
              <LucidePlus class="h-4 w-4" />
            </button>
          </div>

          <div class="flex-1 space-y-2 overflow-y-auto px-2 pb-3">
            <button
              v-if="!group.tasks.length"
              class="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm font-medium text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
              @click="$emit('request-new-task', { status: group.title })"
            >
              <LucidePlus class="h-4 w-4" />
              Add Task
            </button>

            <article
              v-for="d in visibleTasksForGroup(group.tasks)"
              :key="d.name"
              draggable="true"
              class="group cursor-grab rounded-lg border border-outline-gray-2 bg-surface-white p-3 shadow-sm transition hover:border-outline-gray-3 hover:shadow active:cursor-grabbing"
              :class="[
                isSelected(d.name) ? 'ring-2 ring-outline-gray-4' : '',
                draggedTask?.name === d.name ? 'opacity-50' : '',
              ]"
              @dragstart="onDragStart(d, $event)"
              @dragend="onDragEnd"
              @click="$router.push(taskRoute(d))"
            >
              <div class="mb-2 flex items-start gap-2">
                <label class="mt-0.5 flex shrink-0 cursor-pointer items-center" @click.stop>
                  <input
                    type="checkbox"
                    class="h-3.5 w-3.5 cursor-pointer rounded border-gray-300 accent-gray-800 focus:ring-0"
                    :checked="isSelected(d.name)"
                    @change="toggleTask(d.name)"
                  />
                </label>
                <div class="min-w-0 flex-1">
                  <router-link
                    :to="taskRoute(d)"
                    class="line-clamp-2 text-left text-base font-semibold leading-5 text-ink-gray-9 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                    @click.stop
                  >
                    {{ d.title }}
                  </router-link>
                  <div class="mt-1 text-sm text-ink-gray-5">#{{ d.name }}</div>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-1.5 text-sm text-ink-gray-5">
                <template v-if="assigneeIds(d).length">
                  <Tooltip
                    v-for="(uid, idx) in visibleAssigneeIds(d)"
                    :key="uid + '-' + idx"
                    :text="$user(uid).full_name"
                  >
                    <UserAvatar class="shrink-0" :user="uid" size="sm" />
                  </Tooltip>
                </template>
                <span v-if="d.due_date" class="inline-flex items-center gap-1 rounded border border-outline-gray-2 px-1.5 py-0.5" :class="isTaskOverdue(d) ? 'text-red-500' : ''">
                  <LucideCalendar class="h-3 w-3" />
                  {{ $dayjs(d.due_date).format('D MMM') }}
                </span>
                <span v-if="d.priority" class="inline-flex items-center gap-1 rounded border border-outline-gray-2 px-1.5 py-0.5">
                  <LucideFlag class="h-3 w-3" :class="priorityIconClass(d.priority)" />
                  {{ d.priority }}
                </span>
              </div>

              <div class="mt-3 flex items-center justify-between gap-2">
                <Dropdown :options="statusOptions({ onClick: (status) => tasksResource.setValue.submit({ status, name: d.name }) })">
                  <button class="flex items-center gap-1 rounded px-1.5 py-1 text-sm text-ink-gray-6 hover:bg-surface-gray-2" @click.stop>
                    <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" />
                    {{ d.status || '—' }}
                  </button>
                </Dropdown>
                <span class="text-xs text-ink-gray-4">{{ $dayjs(d.modified).fromNow() }}</span>
              </div>
            </article>

            <button
              v-if="group.tasks.length"
              class="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm font-medium text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
              @click="$emit('request-new-task', { status: group.title })"
            >
              <LucidePlus class="h-4 w-4" />
              Add Task
            </button>
          </div>
        </section>
      </div>
    </div>


  </div>
</template>

<script>
import { Dropdown, Tooltip } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import UserAvatar from './UserAvatar.vue'

export default {
  name: 'KanbanView',
  components: {
    Dropdown,
    Tooltip,
    TaskStatusIcon,
    UserAvatar,
  },
  props: {
    tasksResource: { type: Object, required: true },
    kanbanGroups: { type: Array, required: true },
    visibleTasksForGroup: { type: Function, required: true },
    isSelected: { type: Function, required: true },
    toggleTask: { type: Function, required: true },
    taskRoute: { type: Function, required: true },
    assigneeIds: { type: Function, required: true },
    visibleAssigneeIds: { type: Function, required: true },
    isTaskOverdue: { type: Function, required: true },
    priorityIconClass: { type: Function, required: true },
    statusOptions: { type: Function, required: true },
    kanbanColumnClass: { type: Function, required: true },
  },
  emits: ['request-new-task'],
  data() {
    return {
      draggedTask: null,
      dragOverStatus: null,
    }
  },
  methods: {
    onDragStart(task, event) {
      this.draggedTask = task
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', task.name)
    },
    onColumnDragOver(status) {
      if (!this.draggedTask) return
      this.dragOverStatus = status
    },
    onColumnDragLeave(status, event) {
      if (this.dragOverStatus !== status) return
      if (event.currentTarget.contains(event.relatedTarget)) return
      this.dragOverStatus = null
    },
    async onDrop(status) {
      if (!this.draggedTask) return
      const task = this.draggedTask
      this.draggedTask = null
      this.dragOverStatus = null
      if (task.status === status) return
      await this.tasksResource.setValue.submit({ name: task.name, status })
      this.tasksResource.reload()
    },
    onDragEnd() {
      this.draggedTask = null
      this.dragOverStatus = null
    },
  },
}
</script>
