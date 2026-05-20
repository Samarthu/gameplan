<template>
  <div>
    <KanbanView
      v-if="tasks.data?.length && viewMode === 'kanban'"
      :tasksResource="tasks"
      :kanbanGroups="kanbanGroups"
      :childTasksByParent="childTasksByParent"
      :isSelected="isSelected"
      :toggleTask="toggleTask"
      :taskRoute="taskRoute"
      :assigneeIds="assigneeIds"
      :visibleAssigneeIds="visibleAssigneeIds"
      :isTaskOverdue="isTaskOverdue"
      :priorityIconClass="priorityIconClass"
      :statusOptions="statusOptions"
      :taskTypeOptions="taskTypeOptions"
      :kanbanColumnClass="kanbanColumnClass"
      :userOptions="userOptions"
      :setAssignee="setAssignee"
      :priorityOptions="priorityOptions"
      :setDueDate="setDueDate"
      :canDeleteTask="canDeleteTask"
      :confirmDeleteTask="confirmDeleteTask"
      @request-new-task="$emit('request-new-task', $event)"
    />

    <TeamView
      v-else-if="tasks.data?.length && viewMode === 'team'"
      :tasks="topLevelTasks"
      :assigneeIds="assigneeIds"
      :taskRoute="taskRoute"
      :isTaskOverdue="isTaskOverdue"
    />

    <ListView
      v-else-if="tasks.data?.length"
      :tasksResource="tasks"
      :groupedTasks="groupedTasks"
      :compact="compact"
      :columns="columns"
      :isOpen="isOpen"
      :horizontalScrollLeft="horizontalScrollLeft"
      :showColumnsPicker="showColumnsPicker"
      :columnsPickerStyle="columnsPickerStyle"
      :inlinePopover="inlinePopover"
      :userOptions="userOptions"
      :syncGroupHeaderScroll="syncGroupHeaderScroll"
      :visibleTasksForGroup="visibleTasksForGroup"
      :isGroupFullySelected="isGroupFullySelected"
      :isGroupPartiallySelected="isGroupPartiallySelected"
      :toggleGroup="toggleGroup"
      :isSelected="isSelected"
      :toggleTask="toggleTask"
      :taskRoute="taskRoute"
      :isTaskOverdue="isTaskOverdue"
      :statusOptions="statusOptions"
      :taskTypeOptions="taskTypeOptions"
      :hasChildTasks="hasChildTasks"
      :isChildTasksOpen="isChildTasksOpen"
      :toggleChildTasks="toggleChildTasks"
      :taskDepth="taskDepth"
      :assigneeIds="assigneeIds"
      :assigneeStackSpacingClass="assigneeStackSpacingClass"
      :visibleAssigneeIds="visibleAssigneeIds"
      :extraAssigneeCount="extraAssigneeCount"
      :extraAssigneeNames="extraAssigneeNames"
      :toggleInlinePopover="toggleInlinePopover"
      :setAssignee="setAssignee"
      :priorityOptions="priorityOptions"
      :setDueDate="setDueDate"
      :canDeleteTask="canDeleteTask"
      :confirmDeleteTask="confirmDeleteTask"
      :toggleColumn="toggleColumn"
      :toggleColumnsPicker="toggleColumnsPicker"
    />

    <div
      class="flex flex-col items-center py-8 text-base border-2 border-dashed rounded-lg text-ink-gray-5"
      v-else
    >
      No tasks
    </div>

    <!-- Bulk action bar -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="translate-y-2 opacity-0"
        enter-to-class="translate-y-0 opacity-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="translate-y-0 opacity-100"
        leave-to-class="translate-y-2 opacity-0"
      >
        <div
          v-if="selectedTasks.length > 0"
          class="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-xl border border-outline-gray-2 bg-surface-white px-4 py-2.5 shadow-2xl"
        >
          <span class="mr-1 text-sm font-medium whitespace-nowrap text-ink-gray-7">
            {{ selectedTasks.length }} selected
          </span>
          <div class="w-px h-4 bg-outline-gray-2"></div>

          <!-- Status -->
          <Dropdown :options="bulkStatusOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideCircleDot class="h-3.5 w-3.5" />
              Status
            </button>
          </Dropdown>

          <!-- Type -->
          <Dropdown :options="bulkTaskTypeOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideCircle class="h-3.5 w-3.5" />
              Type
            </button>
          </Dropdown>

          <!-- Priority -->
          <Dropdown :options="bulkPriorityOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
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
              class="absolute p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <input
                type="date"
                class="block px-2 py-1 text-sm border rounded-md border-outline-gray-2 text-ink-gray-9 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
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
              class="absolute w-56 p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <Autocomplete
                :options="projectOptions"
                placeholder="Search project..."
                @update:modelValue="bulkSetProject"
              />
            </div>
          </div>

          <div class="w-px h-4 bg-outline-gray-2"></div>

          <!-- Delete -->
          <button
            class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-red-500 transition hover:bg-surface-red-1"
            @click="confirmBulkDelete"
          >
            <LucideTrash2 class="h-3.5 w-3.5" />
            Delete
          </button>

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
import { Dropdown, Autocomplete } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import ListView from './ListView.vue'
import KanbanView from './KanbanView.vue'
import TeamView from './TeamView.vue'
import { activeProjects } from '@/data/projects'
import { activeUsers } from '@/data/users'

const COLUMNS_STORAGE_KEY = 'gameplan_task_columns'
const TASK_TYPES = ['Task', 'Milestone', 'Bug', 'Event', 'Form Response', 'Meeting Note', 'Request']

export default {
  name: 'TaskList',
  props: {
    viewMode: {
      type: String,
      default: 'list',
    },
    groupByStatus: {
      type: Boolean,
      default: false,
    },
    listOptions: {
      type: Object,
      default: () => ({}),
    },
    compact: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    let saved = {}
    try {
      saved = JSON.parse(localStorage.getItem(COLUMNS_STORAGE_KEY) || '{}')
    } catch {}
    return {
      isOpen: {
        Backlog: true,
        Todo: true,
        'In Progress': true,
        'Under Testing': true,
        'Ready to Merge': true,
        Reopen: true,
        Cancelled: true,
        Done: true,
      },
      selectedTasks: [],
      openChildTasks: {},
      horizontalScrollLeft: 0,
      activePopover: null,
      showColumnsPicker: false,
      columnsPickerStyle: {},
      inlinePopover: { name: null, field: null },
      columns: {
        assignee:   { label: 'Assignee',    visible: saved.assignee   ?? true },
        priority:   { label: 'Priority',    visible: saved.priority   ?? true },
        due_date:   { label: 'Due Date',    visible: saved.due_date   ?? true },
        status:     { label: 'Status',      visible: saved.status     ?? false },
        modified:   { label: 'Modified',    visible: saved.modified   ?? true },
        created_by: { label: 'Created By',  visible: saved.created_by ?? false },
      },
    }
  },
  mounted() {
    document.addEventListener('click', this.handleOutsideClick)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick)
  },
  components: {
    Dropdown,
    Autocomplete,
    TaskStatusIcon,
    ListView,
    KanbanView,
    TeamView,
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
        pageLength: this.listOptions.pageLength || 1000,
        auto: true,
        realtime: true,
      }
    },
  },
  methods: {
    syncGroupHeaderScroll(event) {
      this.horizontalScrollLeft = event.target.scrollLeft
    },
    hasChildTasks(task) {
      return Boolean(this.childTasksByParent[task.name]?.length)
    },
    isChildTasksOpen(taskName) {
      return Boolean(this.openChildTasks[taskName])
    },
    toggleChildTasks(taskName) {
      this.openChildTasks = {
        ...this.openChildTasks,
        [taskName]: !this.openChildTasks[taskName],
      }
    },
    visibleTasksForGroup(tasks) {
      return this.collectVisibleTasks(tasks)
    },
    collectVisibleTasks(tasks, depth = 0, visited = new Set()) {
      const visibleTasks = []
      for (const task of tasks) {
        if (visited.has(task.name)) continue
        visited.add(task.name)
        visibleTasks.push({ ...task, _depth: depth })
        if (this.isChildTasksOpen(task.name)) {
          visibleTasks.push(
            ...this.collectVisibleTasks(
              this.childTasksByParent[task.name] || [],
              depth + 1,
              visited,
            ),
          )
        }
      }
      return visibleTasks
    },
    taskDepth(task) {
      return Number(task._depth || 0)
    },
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
      return ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Reopen'].map((status) => {
        return {
          icon: () => h(TaskStatusIcon, { status }),
          label: status,
          onClick: () => onClick(status),
        }
      })
    },
    taskTypeOptions({ onClick }) {
      return TASK_TYPES.map((taskType) => ({
        label: taskType,
        onClick: () => onClick(taskType),
      }))
    },
    toggleColumn(key) {
      this.columns[key].visible = !this.columns[key].visible
      const toSave = {}
      for (const [k, v] of Object.entries(this.columns)) toSave[k] = v.visible
      localStorage.setItem(COLUMNS_STORAGE_KEY, JSON.stringify(toSave))
    },
    toggleColumnsPicker(event) {
      if (!this.showColumnsPicker && event?.currentTarget) {
        const rect = event.currentTarget.getBoundingClientRect()
        this.columnsPickerStyle = {
          top: `${rect.bottom + 4}px`,
          right: `${Math.max(window.innerWidth - rect.right, 8)}px`,
        }
      }
      this.showColumnsPicker = !this.showColumnsPicker
    },
    handleOutsideClick(e) {
      if (this.showColumnsPicker) {
        this.showColumnsPicker = false
      }
      if (this.inlinePopover.name) {
        this.inlinePopover = { name: null, field: null }
      }
    },
    toggleInlinePopover(taskName, field) {
      if (this.inlinePopover.name === taskName && this.inlinePopover.field === field) {
        this.inlinePopover = { name: null, field: null }
      } else {
        this.inlinePopover = { name: taskName, field }
      }
    },
    setDueDate(task, date) {
      this.inlinePopover = { name: null, field: null }
      this.tasks.setValue.submit({ name: task.name, due_date: date || null })
    },
    setAssignee(task, option) {
      if (!option) return
      this.inlinePopover = { name: null, field: null }
      const existing = this.assigneeIds(task)
      if (existing.includes(option.value)) return
      const merged = [...existing, option.value]
      this.tasks.setValue.submit({
        name: task.name,
        assignees: merged.map((user) => ({ user })),
      })
    },
    priorityOptions(task) {
      return ['Urgent', 'High', 'Medium', 'Low'].map((p) => ({
        label: p,
        onClick: () => this.tasks.setValue.submit({ name: task.name, priority: p }),
      }))
    },
    priorityIconClass(priority) {
      return {
        Urgent: 'text-red-600',
        High: 'text-red-500',
        Medium: 'text-amber-500',
        Low: 'text-ink-gray-5',
      }[priority] || 'text-ink-gray-5'
    },
    kanbanColumnClass(status) {
      return {
        Backlog: 'bg-surface-gray-1',
        Todo: 'bg-amber-50',
        'In Progress': 'bg-pink-50',
        'Under Testing': 'bg-surface-blue-1',
        'Ready to Merge': 'bg-green-50',
        Done: 'bg-green-50',
        Cancelled: 'bg-surface-red-1',
        Reopen: 'bg-orange-50',
      }[status] || 'bg-surface-gray-1'
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
      this.tasks.reload()
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
    canDeleteTask(task) {
      const user = this.$user('sessionUser')
      return (
        task.owner === user.name ||
        user.name === 'Administrator' ||
        user.role === 'Gameplan Admin' ||
        user.is_system_manager
      )
    },
    confirmDeleteTask(task) {
      this.$dialog({
        title: 'Delete task',
        message: 'Are you sure you want to delete this task?',
        actions: [
          {
            label: 'Delete',
            theme: 'red',
            variant: 'solid',
            onClick: (close) => {
              return this.tasks.delete.submit(task.name, {
                onSuccess: () => {
                  close()
                  this.selectedTasks = this.selectedTasks.filter((name) => name !== task.name)
                  this.tasks.reload()
                },
              })
            },
          },
        ],
      })
    },
    confirmBulkDelete() {
      const deletableTasks = this.selectedTaskDocs.filter((task) => this.canDeleteTask(task))
      const skippedCount = this.selectedTasks.length - deletableTasks.length

      if (!deletableTasks.length) {
        this.$dialog({
          title: 'Cannot delete tasks',
          message: 'You do not have permission to delete the selected tasks.',
        })
        return
      }

      const taskLabel = deletableTasks.length === 1 ? 'task' : 'tasks'
      const skippedMessage = skippedCount
        ? ` ${skippedCount} selected ${skippedCount === 1 ? 'task is' : 'tasks are'} not deletable and will be skipped.`
        : ''

      this.$dialog({
        title: `Delete ${deletableTasks.length} ${taskLabel}`,
        message: `Are you sure you want to delete ${deletableTasks.length} selected ${taskLabel}?${skippedMessage}`,
        actions: [
          {
            label: 'Delete',
            theme: 'red',
            variant: 'solid',
            onClick: async (close) => {
              for (const task of deletableTasks) {
                await this.tasks.delete.submit(task.name)
              }
              close()
              this.clearSelection()
              this.tasks.reload()
            },
          },
        ],
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
      return this.assigneeIds(task).slice(0, 3)
    },
    extraAssigneeCount(task) {
      const n = this.assigneeIds(task).length
      return n > 3 ? n - 3 : 0
    },
    extraAssigneeNames(task) {
      return this.assigneeIds(task)
        .slice(3)
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
    userOptions() {
      return activeUsers.value.map((u) => ({
        label: u.full_name || u.name,
        value: u.name,
      }))
    },
    selectedTaskDocs() {
      const selected = new Set(this.selectedTasks)
      return (this.tasks.data || []).filter((task) => selected.has(task.name))
    },
    bulkStatusOptions() {
      return this.statusOptions({ onClick: (status) => this.bulkUpdate('status', status) })
    },
    bulkTaskTypeOptions() {
      return this.taskTypeOptions({ onClick: (task_type) => this.bulkUpdate('task_type', task_type) })
    },
    bulkPriorityOptions() {
      return [
        { label: 'Urgent', onClick: () => this.bulkUpdate('priority', 'Urgent') },
        { label: 'High',   onClick: () => this.bulkUpdate('priority', 'High') },
        { label: 'Medium', onClick: () => this.bulkUpdate('priority', 'Medium') },
        { label: 'Low',    onClick: () => this.bulkUpdate('priority', 'Low') },
      ]
    },
    groupedTasks() {
      if (!this.groupByStatus) {
        return [{ id: 'all', title: '', tasks: this.topLevelTasks }]
      }
      return ['In Progress', 'Under Testing', 'Ready to Merge', 'Todo', 'Backlog', 'Done', 'Cancelled', 'Reopen'].map((status) => {
        return {
          id: status,
          title: status,
          tasks: this.tasksByStatus[status] || [],
        }
      })
    },
    kanbanGroups() {
      return ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Reopen'].map((status) => {
        return {
          id: status,
          title: status,
          tasks: this.tasksByStatus[status] || [],
        }
      })
    },
    tasksByStatus() {
      const tasksByStatus = {}
      this.topLevelTasks.forEach((task) => {
        if (!tasksByStatus[task.status]) {
          tasksByStatus[task.status] = []
        }
        tasksByStatus[task.status].push(task)
      })
      return tasksByStatus
    },
    childTasksByParent() {
      return (this.tasks.data || []).reduce((childrenByParent, task) => {
        if (!task.parent_task) return childrenByParent
        if (!childrenByParent[task.parent_task]) {
          childrenByParent[task.parent_task] = []
        }
        childrenByParent[task.parent_task].push(task)
        return childrenByParent
      }, {})
    },
    topLevelTasks() {
      return (this.tasks.data || []).filter((task) => !task.parent_task)
    },
  },
}
</script>
