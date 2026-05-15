<template>
  <div>
    <div class="@container" v-if="tasks.data?.length">
      <div v-for="group in groupedTasks" :key="group.title">
        <button
          class="group flex w-full items-baseline rounded-sm bg-surface-menu-bar px-2.5 py-2 text-base transition hover:bg-surface-gray-2"
          v-if="group.title && group.tasks.length"
          @click="isOpen[group.title] = !isOpen[group.title]"
        >
          <label class="mr-2 flex items-center" @click.stop>
            <input
              type="checkbox"
              class="h-3.5 w-3.5 rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
              :checked="isGroupFullySelected(group)"
              :indeterminate.prop="isGroupPartiallySelected(group)"
              @change="toggleGroup(group)"
            />
          </label>
          <span class="font-medium text-ink-gray-9">
            {{ group.title }}
          </span>
          <span class="ml-2 text-sm text-ink-gray-5">{{ group.tasks.length }}</span>
          <span class="ml-auto hidden text-sm text-ink-gray-5 group-hover:inline">
            {{ isOpen[group.title] ? 'Collapse' : 'Expand' }}
          </span>
        </button>
        <div :class="{ hidden: !(isOpen[group.title] ?? true) }">
          <div v-for="(d, index) in group.tasks" :key="d.name">
            <div
              class="flex items-center rounded transition"
              :class="isSelected(d.name) ? 'bg-surface-blue-1' : 'hover:bg-surface-gray-2'"
            >
              <label class="flex shrink-0 cursor-pointer items-center px-2.5 py-2" @click.stop>
                <input
                  type="checkbox"
                  class="h-4 w-4 cursor-pointer rounded border-gray-300 accent-gray-800 focus:ring-0"
                  :checked="isSelected(d.name)"
                  @change="toggleTask(d.name)"
                />
              </label>
              <!-- Status icon outside router-link to avoid click conflicts -->
              <div class="flex shrink-0 items-center px-1 py-2">
                <LoadingIndicator
                  class="h-4 w-4 text-ink-gray-5"
                  v-if="tasks.delete.loading && tasks.delete.params.name === d.name"
                />
                <Tooltip text="Change status" v-else>
                  <Dropdown
                    :options="
                      statusOptions({
                        onClick: (status) =>
                          tasks.setValue.submit({
                            status,
                            name: d.name,
                          }),
                      })
                    "
                  >
                    <button
                      class="flex rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                    >
                      <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" />
                    </button>
                  </Dropdown>
                </Tooltip>
              </div>
              <router-link
                :to="taskRoute(d)"
                class="flex h-15 min-w-0 flex-1 items-center py-2 pr-2.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                :class="{
                  'pointer-events-none': tasks.delete.loading && tasks.delete.params.name === d.name,
                }"
              >
                <div class="w-full">
                  <div class="flex min-w-0 items-start">
                    <div
                      class="overflow-hidden text-ellipsis whitespace-nowrap text-base font-medium leading-4 text-ink-gray-9"
                    >
                      {{ d.title }}
                    </div>
                    <div class="ml-auto shrink-0 whitespace-nowrap text-sm text-ink-gray-5">
                      {{ $dayjs(d.modified).fromNow() }}
                    </div>
                  </div>

                  <div class="mt-1.5 flex items-center">
                    <div class="text-base text-ink-gray-5">#{{ d.name }}</div>
                    <div
                      v-if="$route.name != 'ProjectOverview' && d.project"
                      class="flex min-w-0 flex-1 items-center text-base leading-none text-ink-gray-5"
                    >
                      <div class="px-2 leading-none text-ink-gray-5">&middot;</div>
                      <div>{{ d.team_title }}</div>
                      <LucideChevronRight class="h-3 w-3 shrink-0 text-ink-gray-5" />
                      <div class="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap">
                        {{ d.project_title }}
                      </div>
                    </div>
                    <div
                      class="hidden shrink-0 items-center @md:flex"
                      v-if="assigneeIds(d).length"
                    >
                      <div class="px-2 leading-none text-ink-gray-5">&middot;</div>
                      <div class="flex shrink-0 items-center">
                        <div
                          class="flex shrink-0 items-center"
                          :class="assigneeStackSpacingClass(d)"
                        >
                          <Tooltip
                            v-for="(uid, idx) in visibleAssigneeIds(d)"
                            :key="uid + '-' + idx"
                            :text="$user(uid).full_name"
                          >
                            <span
                              class="relative inline-flex rounded-full ring-2 ring-surface-white"
                              :style="{ zIndex: 10 + idx }"
                            >
                              <UserAvatar class="shrink-0" :user="uid" size="sm" />
                            </span>
                          </Tooltip>
                          <Tooltip
                            v-if="extraAssigneeCount(d) > 0"
                            :text="extraAssigneeNames(d)"
                          >
                            <span
                              class="relative z-10 inline-flex h-5 min-w-[1.25rem] shrink-0 items-center justify-center rounded-full bg-surface-gray-3 px-1 text-xs font-medium text-ink-gray-8 ring-2 ring-surface-white"
                            >
                              +{{ extraAssigneeCount(d) }}
                            </span>
                          </Tooltip>
                        </div>
                      </div>
                    </div>

                    <template v-if="d.due_date">
                      <div class="px-2 leading-none text-ink-gray-5">&middot;</div>
                      <div class="flex items-center">
                        <LucideCalendar class="h-3 w-3 text-ink-gray-5" />
                        <span class="ml-2 whitespace-nowrap text-base text-ink-gray-5">
                          {{ $dayjs(d.due_date).format('D MMM') }}
                        </span>
                      </div>
                    </template>
                    <template v-if="d.priority">
                      <div class="px-2 leading-none text-ink-gray-5">&middot;</div>
                      <div class="flex items-center">
                        <div
                          class="h-2 w-2 rounded-full"
                          :class="{
                            'bg-surface-red-5': d.priority === 'High',
                            'bg-surface-amber-3': d.priority === 'Medium',
                            'bg-surface-gray-5': d.priority === 'Low',
                          }"
                        ></div>
                        <span class="ml-2 text-base text-ink-gray-5">
                          {{ d.priority }}
                        </span>
                      </div>
                    </template>
                    <div
                      class="ml-auto inline-grid h-4 w-4 shrink-0 place-items-center rounded-full bg-surface-gray-3 text-xs"
                      :class="[
                        d.unread ? 'text-ink-gray-9' : 'text-ink-gray-5',
                        d.comments_count ? '' : 'invisible',
                      ]"
                    >
                      {{ d.comments_count || 0 }}
                    </div>
                  </div>
                </div>
              </router-link>
            </div>
            <div class="mx-2.5 border-b" v-if="index < group.tasks.length - 1"></div>
          </div>
        </div>
      </div>
    </div>
    <div
      class="flex flex-col items-center rounded-lg border-2 border-dashed py-8 text-base text-ink-gray-5"
      v-else
    >
      No tasks
    </div>

    <!-- Bulk action bar -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition ease-out duration-150"
        enter-from-class="opacity-0 translate-y-2"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-100"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-2"
      >
        <div
          v-if="selectedTasks.length > 0"
          class="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-xl border border-outline-gray-2 bg-surface-white px-4 py-2.5 shadow-2xl"
        >
          <span class="mr-1 whitespace-nowrap text-sm font-medium text-ink-gray-7">
            {{ selectedTasks.length }} selected
          </span>
          <div class="h-4 w-px bg-outline-gray-2"></div>

          <!-- Status -->
          <Dropdown :options="bulkStatusOptions">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
            >
              <LucideCircleDot class="h-3.5 w-3.5" />
              Status
            </button>
          </Dropdown>

          <!-- Priority -->
          <Dropdown :options="bulkPriorityOptions">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
            >
              <LucideFlag class="h-3.5 w-3.5" />
              Priority
            </button>
          </Dropdown>

          <!-- Due Date -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('date')"
            >
              <LucideCalendar class="h-3.5 w-3.5" />
              Due Date
            </button>
            <div
              v-if="activePopover === 'date'"
              class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-lg"
            >
              <input
                type="date"
                class="block rounded-md border border-outline-gray-2 px-2 py-1 text-sm text-ink-gray-9 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                @change="bulkSetDueDate($event.target.value)"
              />
            </div>
          </div>

          <!-- Project -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('project')"
            >
              <LucideFolderOpen class="h-3.5 w-3.5" />
              Project
            </button>
            <div
              v-if="activePopover === 'project'"
              class="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 w-56 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-lg"
            >
              <Autocomplete
                :options="projectOptions"
                placeholder="Search project..."
                @update:modelValue="bulkSetProject"
              />
            </div>
          </div>

          <div class="h-4 w-px bg-outline-gray-2"></div>

          <!-- Clear -->
          <button
            class="flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-5 transition hover:bg-surface-gray-2 hover:text-ink-gray-7"
            @click="clearSelection"
          >
            <LucideX class="h-3.5 w-3.5" />
            Clear
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
<script>
import { h } from 'vue'
import { LoadingIndicator, Dropdown, Tooltip, Autocomplete } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import UserAvatar from './UserAvatar.vue'
import { activeProjects } from '@/data/projects'

export default {
  name: 'TaskList',
  props: {
    groupByStatus: {
      type: Boolean,
      default: false,
    },
    listOptions: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      isOpen: {
        Backlog: true,
        Todo: true,
        'In Progress': true,
        'Under Testing': true,
        'Ready to Merge': true,
        Cancelled: false,
        Done: false,
      },
      selectedTasks: [],
      activePopover: null,
    }
  },
  components: {
    LoadingIndicator,
    Dropdown,
    Tooltip,
    Autocomplete,
    TaskStatusIcon,
    UserAvatar,
  },
  resources: {
    tasks() {
      return {
        type: 'list',
        url: 'gameplan.gameplan.doctype.gp_task.gp_task.get_list',
        cache: ['Tasks', this.listOptions],
        doctype: 'GP Task',
        fields: ['*', 'project.title as project_title', 'team.title as team_title'],
        filters: this.listOptions.filters,
        orderBy: this.listOptions.orderBy || 'creation desc',
        pageLength: this.listOptions.pageLength || 20,
        auto: true,
        realtime: true,
      }
    },
  },
  methods: {
    taskRoute(task) {
      if (this.$route.name === 'TeamTasks') {
        return {
          name: 'Task',
          params: { taskId: task.name },
        }
      }
      return {
        name: task.project ? 'ProjectTaskDetail' : 'Task',
        params: { teamId: task.team, projectId: task.project, taskId: task.name },
      }
    },
    statusOptions({ onClick }) {
      return ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled'].map((status) => {
        return {
          icon: () => h(TaskStatusIcon, { status }),
          label: status,
          onClick: () => onClick(status),
        }
      })
    },

    // Selection helpers
    isSelected(name) {
      return this.selectedTasks.includes(name)
    },
    toggleTask(name) {
      const idx = this.selectedTasks.indexOf(name)
      if (idx > -1) {
        this.selectedTasks.splice(idx, 1)
      } else {
        this.selectedTasks.push(name)
      }
    },
    isGroupFullySelected(group) {
      return group.tasks.length > 0 && group.tasks.every((t) => this.isSelected(t.name))
    },
    isGroupPartiallySelected(group) {
      return group.tasks.some((t) => this.isSelected(t.name)) && !this.isGroupFullySelected(group)
    },
    toggleGroup(group) {
      if (this.isGroupFullySelected(group)) {
        group.tasks.forEach((t) => {
          const idx = this.selectedTasks.indexOf(t.name)
          if (idx > -1) this.selectedTasks.splice(idx, 1)
        })
      } else {
        group.tasks.forEach((t) => {
          if (!this.isSelected(t.name)) this.selectedTasks.push(t.name)
        })
      }
    },
    clearSelection() {
      this.selectedTasks = []
      this.activePopover = null
    },
    togglePopover(name) {
      this.activePopover = this.activePopover === name ? null : name
    },

    // Bulk actions
    async bulkUpdate(field, value) {
      for (const name of this.selectedTasks) {
        await this.tasks.setValue.submit({ name, [field]: value })
      }
      this.clearSelection()
    },
    bulkSetDueDate(date) {
      this.activePopover = null
      this.bulkUpdate('due_date', date)
    },
    bulkSetProject(option) {
      if (!option) return
      this.activePopover = null
      this.bulkUpdate('project', option.value)
    },

    normalizeUserIdList(val) {
      if (val == null) return []
      if (Array.isArray(val)) return val.filter(Boolean)
      if (typeof val === 'string') {
        const s = val.trim()
        if (!s) return []
        if (s.startsWith('[')) {
          try {
            const p = JSON.parse(s)
            return Array.isArray(p) ? p.filter(Boolean) : []
          } catch {
            return []
          }
        }
        return [s]
      }
      return []
    },
    userIdsFromAssigneesChild(task) {
      const rows = task.assignees
      if (!Array.isArray(rows) || !rows.length) return []
      return rows.map((r) => (typeof r === 'object' && r ? r.user : null)).filter(Boolean)
    },
    assigneeIds(task) {
      const seen = new Set()
      const out = []
      const add = (id) => {
        if (!id || seen.has(id)) return
        seen.add(id)
        out.push(id)
      }
      for (const u of this.userIdsFromAssigneesChild(task)) add(u)
      for (const u of this.normalizeUserIdList(task.assignee_users)) add(u)
      add(task.assigned_to)
      return out
    },
    assigneeStackSpacingClass(task) {
      const n = this.assigneeIds(task).length
      if (n <= 2) return 'gap-1'
      return '-space-x-1.5'
    },
    visibleAssigneeIds(task) {
      return this.assigneeIds(task).slice(0, 4)
    },
    extraAssigneeCount(task) {
      const n = this.assigneeIds(task).length
      return n > 4 ? n - 4 : 0
    },
    extraAssigneeNames(task) {
      return this.assigneeIds(task)
        .slice(4)
        .map((id) => this.$user(id).full_name)
        .filter(Boolean)
        .join(', ')
    },
    isTaskOverdue(task) {
      if (!task.due_date) return false
      if (task.status === 'Done' || task.status === 'Cancelled') return false
      const due = this.$dayjs(task.due_date).startOf('day')
      const today = this.$dayjs().startOf('day')
      return due.isBefore(today)
    },
  },
  computed: {
    tasks() {
      return this.$resources.tasks
    },
    projectOptions() {
      return activeProjects.value.map((p) => ({
        label: p.title,
        value: p.name,
      }))
    },
    bulkStatusOptions() {
      return this.statusOptions({ onClick: (status) => this.bulkUpdate('status', status) })
    },
    bulkPriorityOptions() {
      return [
        {
          label: 'High',
          onClick: () => this.bulkUpdate('priority', 'High'),
        },
        {
          label: 'Medium',
          onClick: () => this.bulkUpdate('priority', 'Medium'),
        },
        {
          label: 'Low',
          onClick: () => this.bulkUpdate('priority', 'Low'),
        },
      ]
    },
    groupedTasks() {
      if (!this.groupByStatus) {
        return [
          {
            id: 'all',
            title: '',
            tasks: this.tasks.data,
          },
        ]
      }
      return ['In Progress', 'Under Testing', 'Ready to Merge', 'Todo', 'Backlog', 'Done', 'Cancelled'].map((status) => {
        return {
          id: status,
          title: status,
          tasks: this.tasksByStatus[status] || [],
        }
      })
    },
    tasksByStatus() {
      const tasksByStatus = {}
      this.tasks.data.forEach((task) => {
        if (!tasksByStatus[task.status]) {
          tasksByStatus[task.status] = []
        }
        tasksByStatus[task.status].push(task)
      })
      return tasksByStatus
    },
  },
}
</script>
