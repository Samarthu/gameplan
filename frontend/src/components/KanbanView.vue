<template>
  <div>
    <div v-if="tasksResource.data?.length" class="overflow-x-auto pb-3">
      <div class="flex min-h-[calc(100vh-13rem)] gap-3">
        <section
          v-for="group in kanbanGroups"
          :key="group.title"
          class="kanban-column flex w-72 shrink-0 flex-col rounded-lg border border-outline-gray-2 bg-surface-gray-1/70"
          :class="[
            kanbanColumnClass(group.title),
            dragOverStatus === group.title ? 'kanban-column-drop-target ring-2 ring-outline-gray-4' : '',
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

          <div class="flex-1 overflow-y-auto px-2 pb-3">
            <button
              v-if="!group.tasks.length"
              class="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm font-medium text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
              @click="$emit('request-new-task', { status: group.title })"
            >
              <LucidePlus class="h-4 w-4" />
              Add Task
            </button>

            <TransitionGroup name="kanban-card" tag="div" class="space-y-2">
              <article
                v-for="d in group.tasks"
                :key="d.name"
                draggable="true"
                class="kanban-card group cursor-grab rounded-lg border border-outline-gray-2 bg-surface-white p-3 shadow-sm hover:border-outline-gray-3 hover:shadow active:cursor-grabbing"
                :class="[
                  isSelected(d.name) ? 'ring-2 ring-outline-gray-4' : '',
                  draggedTask?.name === d.name ? 'kanban-card-dragging' : '',
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
                <div class="relative" @click.stop>
                  <button
                    class="inline-flex min-h-[1.75rem] items-center gap-1 rounded px-1 py-0.5 hover:bg-surface-gray-2"
                    @click="toggleCardPopover(d.name, 'assignee')"
                  >
                    <template v-if="assigneeIds(d).length">
                      <div class="isolate flex items-center" :class="assigneeStackSpacingClass(d)">
                        <Tooltip
                          v-for="(uid, idx) in visibleAssigneeIds(d)"
                          :key="uid + '-' + idx"
                          :text="$user(uid).full_name"
                        >
                          <span
                            class="group/assignee relative inline-grid h-6 w-6 place-items-center overflow-hidden rounded-full border-2 border-white text-sm font-medium shadow-sm ring-1"
                            :class="assigneeHeatClass(uid)"
                            :style="{ ...assigneeHeatStyle(uid), zIndex: idx + 1 }"
                          >
                            <img
                              v-if="$user(uid).user_image"
                              :src="$user(uid).user_image"
                              :alt="$user(uid).full_name"
                              class="absolute inset-0 h-full w-full rounded-full object-cover"
                            />
                            <template v-else>{{ userInitial(uid) }}</template>
                            <button
                              type="button"
                              class="absolute -right-1 -top-1 z-10 hidden h-3.5 w-3.5 items-center justify-center rounded-full border border-white bg-ink-gray-8 text-white shadow-sm transition hover:bg-red-600 group-hover/assignee:flex"
                              :aria-label="`Remove ${$user(uid).full_name}`"
                              @click.stop="removeAssignee(d, uid)"
                            >
                              <LucideX class="h-2.5 w-2.5" />
                            </button>
                          </span>
                        </Tooltip>
                        <Tooltip v-if="extraAssigneeCount(d) > 0" :text="extraAssigneeNames(d)">
                          <span
                            class="relative inline-grid h-6 min-w-6 shrink-0 place-items-center rounded-full border-2 border-white px-1 text-xs font-semibold text-white shadow-sm ring-1"
                            :style="{
                              backgroundColor: '#1f2937',
                              '--tw-ring-color': '#111827',
                              zIndex: visibleAssigneeIds(d).length + 1,
                            }"
                          >
                            +{{ extraAssigneeCount(d) }}
                          </span>
                        </Tooltip>
                      </div>
                    </template>
                    <span v-else class="text-sm text-ink-gray-4">Unassigned</span>
                  </button>
                  <div
                    v-if="cardPopover.name === d.name && cardPopover.field === 'assignee'"
                    class="absolute left-0 top-full z-20 mt-1 w-52 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-lg"
                  >
                    <Autocomplete
                      :options="userOptions"
                      placeholder="Search user..."
                      @update:modelValue="(opt) => setAssignee(d, opt)"
                    />
                  </div>
                </div>

                <div @click.stop>
                  <Dropdown :options="taskTypeOptions({ onClick: (task_type) => tasksResource.setValue.submit({ task_type, name: d.name }) })">
                    <button
                      class="inline-flex items-center gap-1 rounded border border-outline-gray-2 px-1.5 py-0.5 hover:bg-surface-gray-2"
                    >
                      <LucideCircle class="h-3 w-3" />
                      {{ d.task_type || 'Task' }}
                    </button>
                  </Dropdown>
                </div>

                <div class="relative" @click.stop>
                  <button
                    class="inline-flex items-center gap-1 rounded border border-outline-gray-2 px-1.5 py-0.5 hover:bg-surface-gray-2"
                    :class="d.due_date && isTaskOverdue(d) ? 'text-red-500' : ''"
                    @click="toggleCardPopover(d.name, 'due_date')"
                  >
                    <LucideCalendar class="h-3 w-3" />
                    {{ d.due_date ? $dayjs(d.due_date).format('D MMM') : 'Due Date' }}
                  </button>
                  <div
                    v-if="cardPopover.name === d.name && cardPopover.field === 'due_date'"
                    class="absolute left-0 top-full z-20 mt-1 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-lg"
                  >
                    <input
                      type="date"
                      :value="d.due_date"
                      class="block rounded-md border border-outline-gray-2 px-2 py-1 text-sm text-ink-gray-9 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                      @change="setCardDueDate(d, $event.target.value)"
                    />
                    <button
                      v-if="d.due_date"
                      class="mt-1 w-full rounded px-2 py-1 text-xs text-ink-gray-5 hover:bg-surface-gray-2"
                      @click="setCardDueDate(d, '')"
                    >
                      Clear date
                    </button>
                  </div>
                </div>

                <div @click.stop>
                  <Dropdown :options="priorityOptions(d)">
                    <button
                      class="inline-flex items-center gap-1 rounded border border-outline-gray-2 px-1.5 py-0.5 hover:bg-surface-gray-2"
                    >
                      <LucideFlag class="h-3 w-3" :class="priorityIconClass(d.priority)" />
                      {{ d.priority || 'Priority' }}
                    </button>
                  </Dropdown>
                </div>
              </div>

              <div class="mt-3 flex items-center justify-between gap-2">
                <div @click.stop>
                  <Dropdown :options="statusOptions({ name: d.name, onClick: (status) => tasksResource.setValue.submit({ status, name: d.name }) })">
                    <button class="flex items-center gap-1 rounded px-1.5 py-1 text-sm text-ink-gray-6 hover:bg-surface-gray-2">
                      <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" />
                      {{ d.status || '—' }}
                    </button>
                  </Dropdown>
                </div>
                <div class="flex items-center gap-1">
                  <span class="text-xs text-ink-gray-4">{{ $dayjs(d.modified).fromNow() }}</span>
                  <Tooltip text="Delete task" v-if="canDeleteTask(d)">
                    <button
                      class="grid h-6 w-6 shrink-0 place-items-center rounded text-ink-gray-4 hover:bg-surface-red-1 hover:text-red-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                      :disabled="tasksResource.delete.loading && tasksResource.delete.params.name === d.name"
                      @click.stop="confirmDeleteTask(d)"
                    >
                      <LucideTrash2 class="h-3.5 w-3.5" />
                    </button>
                  </Tooltip>
                </div>
              </div>

              <div
                v-if="childTasks(d).length"
                class="mt-3 border-t border-outline-gray-2 pt-2"
                @click.stop
              >
                <div class="mb-1.5 text-xs font-medium text-ink-gray-5">
                  Sub tasks
                </div>
                <div class="space-y-1">
                  <button
                    v-for="child in childTasks(d)"
                    :key="child.name"
                    class="flex w-full items-start gap-2 rounded px-1.5 py-1.5 text-left hover:bg-surface-gray-2"
                    @click="$router.push(taskRoute(child))"
                  >
                    <TaskStatusIcon
                      :status="child.status"
                      :overdue="isTaskOverdue(child)"
                      class="mt-0.5 shrink-0"
                    />
                    <div class="min-w-0 flex-1">
                      <div class="truncate text-sm font-medium text-ink-gray-8">
                        {{ child.title }}
                      </div>
                      <div class="mt-0.5 flex items-center justify-between gap-2 text-xs text-ink-gray-5">
                        <span>#{{ child.name }}</span>
                        <span class="shrink-0">{{ child.status || '—' }}</span>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
              </article>
            </TransitionGroup>

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
import { Autocomplete, Dropdown, Tooltip } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import UserAvatar from './UserAvatar.vue'
import LucideX from '~icons/lucide/x'

export default {
  name: 'KanbanView',
  components: {
    Dropdown,
    Autocomplete,
    Tooltip,
    TaskStatusIcon,
    UserAvatar,
    LucideX,
  },
  props: {
    tasksResource: { type: Object, required: true },
    kanbanGroups: { type: Array, required: true },
    childTasksByParent: { type: Object, required: true },
    isSelected: { type: Function, required: true },
    toggleTask: { type: Function, required: true },
    taskRoute: { type: Function, required: true },
    assigneeIds: { type: Function, required: true },
    visibleAssigneeIds: { type: Function, required: true },
    assigneeStackSpacingClass: { type: Function, required: true },
    assigneeHeatClass: { type: Function, required: true },
    assigneeHeatStyle: { type: Function, required: true },
    extraAssigneeCount: { type: Function, required: true },
    extraAssigneeNames: { type: Function, required: true },
    isTaskOverdue: { type: Function, required: true },
    priorityIconClass: { type: Function, required: true },
    statusOptions: { type: Function, required: true },
    taskTypeOptions: { type: Function, required: true },
    kanbanColumnClass: { type: Function, required: true },
    userOptions: { type: Array, required: true },
    setAssignee: { type: Function, required: true },
    removeAssignee: { type: Function, required: true },
    priorityOptions: { type: Function, required: true },
    setDueDate: { type: Function, required: true },
    canDeleteTask: { type: Function, required: true },
    confirmDeleteTask: { type: Function, required: true },
  },
  emits: ['request-new-task', 'request-hold'],
  data() {
    return {
      draggedTask: null,
      dragOverStatus: null,
      cardPopover: { name: null, field: null },
    }
  },
  methods: {
    userInitial(user) {
      const fullName = this.$user(user).full_name || user || ''
      return fullName.trim().charAt(0).toUpperCase()
    },
    childTasks(task) {
      return this.childTasksByParent[task.name] || []
    },
    onDragStart(task, event) {
      this.draggedTask = task
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', task.name)
      if (event.dataTransfer.setDragImage) {
        event.dataTransfer.setDragImage(event.currentTarget, 24, 24)
      }
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
      if (status === 'Hold') {
        this.$emit('request-hold', task.name)
        return
      }
      await this.tasksResource.setValue.submit({ name: task.name, status })
      this.tasksResource.reload()
    },
    onDragEnd() {
      this.draggedTask = null
      this.dragOverStatus = null
    },
    toggleCardPopover(taskName, field) {
      if (this.cardPopover.name === taskName && this.cardPopover.field === field) {
        this.cardPopover = { name: null, field: null }
      } else {
        this.cardPopover = { name: taskName, field }
      }
    },
    setCardDueDate(task, date) {
      this.cardPopover = { name: null, field: null }
      this.setDueDate(task, date)
    },
  },
}
</script>

<style scoped>
.kanban-column {
  transition:
    box-shadow 160ms ease,
    border-color 160ms ease,
    transform 160ms ease,
    background-color 160ms ease;
}

.kanban-column-drop-target {
  transform: translateY(-2px);
}

.kanban-card {
  will-change: transform, opacity;
  transition:
    transform 180ms cubic-bezier(0.2, 0, 0, 1),
    opacity 140ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease;
}

.kanban-card:hover {
  transform: translateY(-1px);
}

.kanban-card-dragging {
  opacity: 0.45;
  transform: scale(0.98);
}

.kanban-card-move,
.kanban-card-enter-active,
.kanban-card-leave-active {
  transition:
    transform 220ms cubic-bezier(0.2, 0, 0, 1),
    opacity 160ms ease;
}

.kanban-card-enter-from,
.kanban-card-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}

.kanban-card-leave-active {
  position: absolute;
  width: calc(100% - 1rem);
}
</style>
