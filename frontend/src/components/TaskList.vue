<template>
  <div class="@container" v-if="tasks.data?.length">
    <div v-for="group in groupedTasks" :key="group.title">
      <button
        class="group flex w-full items-baseline rounded-sm bg-surface-menu-bar px-2.5 py-2 text-base transition hover:bg-surface-gray-2"
        v-if="group.title && group.tasks.length"
        @click="isOpen[group.title] = !isOpen[group.title]"
      >
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
          <router-link
            :to="taskRoute(d)"
            class="flex h-15 w-full items-center rounded p-2.5 transition hover:bg-surface-gray-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            :class="{
              'pointer-events-none': tasks.delete.loading && tasks.delete.params.name === d.name,
            }"
          >
            <div class="w-full">
              <div class="flex min-w-0 items-start">
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
                <div
                  class="ml-2.5 overflow-hidden text-ellipsis whitespace-nowrap text-base font-medium leading-4 text-ink-gray-9"
                >
                  {{ d.title }}
                </div>
                <div class="ml-auto shrink-0 whitespace-nowrap text-sm text-ink-gray-5">
                  {{ $dayjs(d.modified).fromNow() }}
                </div>
              </div>

              <div class="ml-6.5 mt-1.5 flex items-center">
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
</template>
<script>
import { h } from 'vue'
import { LoadingIndicator, Dropdown, Tooltip } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import UserAvatar from './UserAvatar.vue'

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
    }
  },
  components: {
    LoadingIndicator,
    Dropdown,
    Tooltip,
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
      return ['Backlog', 'Todo', 'In Progress', 'Done', 'Cancelled'].map((status) => {
        return {
          icon: () => h(TaskStatusIcon, { status }),
          label: status,
          onClick: () => onClick(status),
        }
      })
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
