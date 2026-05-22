<template>
  <div>
    <Teleport to="body">
      <div
        v-if="showFiltersPanel"
        class="fixed z-50 w-[min(56rem,calc(100vw-2rem))] rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xl"
        :style="filtersPanelStyle"
        @click.stop
      >
        <div class="mb-4 flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-semibold text-ink-gray-9">Filters</h3>
            <LucideInfo class="h-3.5 w-3.5 text-ink-gray-4" />
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-1 rounded-lg border border-outline-gray-2 px-2.5 py-1.5 text-sm font-medium text-ink-gray-6 hover:bg-surface-gray-2"
            @click="clearAllFilters"
          >
            Clear
          </button>
        </div>

        <div v-if="taskFilters.length" class="space-y-2">
          <div
            v-for="filter in taskFilters"
            :key="filter.id"
            class="relative grid grid-cols-[minmax(8rem,1fr)_minmax(7rem,0.7fr)_minmax(10rem,1.8fr)_2rem] items-center gap-2 rounded-lg bg-surface-gray-1 p-2"
          >
            <select
              v-model="filter.field"
              class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
              @change="resetFilterValue(filter)"
            >
              <option v-for="field in filterFields" :key="field.value" :value="field.value">
                {{ field.label }}
              </option>
            </select>
            <select
              v-model="filter.operator"
              class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
              @change="resetFilterValue(filter)"
            >
              <option v-for="operator in operatorsForFilter(filter)" :key="operator.value" :value="operator.value">
                {{ operator.label }}
              </option>
            </select>
            <template v-if="filterNeedsValue(filter)">
              <div v-if="isMultiValueFilter(filter) && !isLikeFilter(filter) && valueOptionsForFilter(filter).length" class="relative">
                <button
                  type="button"
                  class="flex h-9 w-full items-center justify-between gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-left text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                  @click.stop="toggleFilterValueMenu(filter.id)"
                >
                  <span class="min-w-0 truncate">
                    {{ selectedFilterValueLabel(filter) || 'Select values' }}
                  </span>
                  <LucideChevronDown class="h-4 w-4 shrink-0 text-ink-gray-5" />
                </button>
                <div
                  v-if="openFilterValueMenu === filter.id"
                  class="absolute left-0 top-full z-50 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-white p-1 shadow-lg"
                  @click.stop
                >
                  <button
                    v-for="option in valueOptionsForFilter(filter)"
                    :key="option.value"
                    type="button"
                    class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-ink-gray-8 hover:bg-surface-gray-2"
                    @click="toggleFilterValue(filter, option.value)"
                  >
                    <span
                      class="grid h-4 w-4 shrink-0 place-items-center rounded-full border"
                      :class="filter.values.includes(option.value) ? 'border-blue-500 bg-blue-500' : 'border-outline-gray-3 bg-surface-white'"
                    >
                      <LucideCheck v-if="filter.values.includes(option.value)" class="h-3 w-3 text-white" />
                    </span>
                    <span class="min-w-0 truncate">{{ option.label }}</span>
                  </button>
                </div>
              </div>
              <select
                v-else-if="!isLikeFilter(filter) && valueOptionsForFilter(filter).length"
                v-model="filter.value"
                class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
              >
                <option value="">Select value</option>
                <option v-for="option in valueOptionsForFilter(filter)" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <input
                v-else
                v-model="filter.value"
                :type="dateFilterFields.includes(filter.field) ? 'date' : 'text'"
                class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                placeholder="Value"
              />
            </template>
            <div v-else class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-4"></div>
            <Tooltip text="Remove filter">
              <button
                type="button"
                class="grid h-8 w-8 place-items-center rounded-lg text-ink-gray-5 hover:bg-surface-red-1 hover:text-red-500"
                aria-label="Remove filter"
                @click="removeTaskFilter(filter.id)"
              >
                <LucideTrash2 class="h-4 w-4" />
              </button>
            </Tooltip>
          </div>
        </div>
        <div v-else class="rounded-lg bg-surface-gray-1 px-3 py-4 text-sm text-ink-gray-5">
          No filters applied
        </div>

        <div class="relative mt-4 inline-block">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm font-medium text-ink-gray-7 shadow-sm hover:bg-surface-gray-2"
            @click.stop="toggleAddFilterMenu"
          >
            <LucidePlus class="h-4 w-4" />
            Add filter
          </button>
          <div
            v-if="showAddFilterMenu"
            class="absolute left-0 top-full z-50 mt-1 max-h-64 w-56 overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-white p-1 shadow-lg"
            @click.stop
          >
            <button
              v-for="field in filterFields"
              :key="field.value"
              type="button"
              class="flex w-full items-center rounded px-2 py-1.5 text-left text-sm text-ink-gray-8 hover:bg-surface-gray-2"
              @click="addTaskFilterForField(field.value)"
            >
              {{ field.label }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <div v-if="selectedTag" class="mb-3 flex flex-wrap items-center gap-2">
      <button
        class="inline-flex items-center gap-1 rounded-full bg-surface-blue-1 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100"
        @click="selectedTag = null"
      >
        <LucideTag class="h-3.5 w-3.5 shrink-0" />
        {{ selectedTag }}
        <LucideX class="h-3.5 w-3.5" />
      </button>
    </div>

    <KanbanView
      v-if="filteredTasks.length && viewMode === 'kanban'"
      :tasksResource="tasks"
      :kanbanGroups="kanbanGroups"
      :childTasksByParent="childTasksByParent"
      :isSelected="isSelected"
      :toggleTask="toggleTask"
      :taskRoute="taskRoute"
      :assigneeIds="assigneeIds"
      :visibleAssigneeIds="visibleAssigneeIds"
      :assigneeStackSpacingClass="assigneeStackSpacingClass"
      :assigneeHeatClass="assigneeHeatClass"
      :assigneeHeatStyle="assigneeHeatStyle"
      :extraAssigneeCount="extraAssigneeCount"
      :extraAssigneeNames="extraAssigneeNames"
      :removeAssignee="removeAssignee"
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
      v-else-if="filteredTasks.length && viewMode === 'team'"
      :tasks="topLevelTasks"
      :assigneeIds="assigneeIds"
      :taskRoute="taskRoute"
      :isTaskOverdue="isTaskOverdue"
    />

    <ListView
      v-else-if="filteredTasks.length"
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
      :assigneeHeatClass="assigneeHeatClass"
      :assigneeHeatStyle="assigneeHeatStyle"
      :extraAssigneeCount="extraAssigneeCount"
      :extraAssigneeNames="extraAssigneeNames"
      :toggleInlinePopover="toggleInlinePopover"
      :setAssignee="setAssignee"
      :removeAssignee="removeAssignee"
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
      {{ tasks.data?.length ? 'No tasks match the selected filters' : 'No tasks' }}
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
          class="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-1.5 rounded-xl border border-outline-gray-2 bg-surface-white px-3 py-2 shadow-2xl"
        >
          <span class="mr-1 whitespace-nowrap text-sm font-medium text-ink-gray-7">
            {{ selectedTasks.length }} selected
          </span>
          <div class="w-px h-4 bg-outline-gray-2"></div>

          <!-- Status -->
          <Dropdown :options="bulkStatusOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideCircleDot class="h-3.5 w-3.5" />
              Status
            </button>
          </Dropdown>

          <!-- Type -->
          <Dropdown :options="bulkTaskTypeOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideCircle class="h-3.5 w-3.5" />
              Type
            </button>
          </Dropdown>

          <!-- Priority -->
          <Dropdown :options="bulkPriorityOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideFlag class="h-3.5 w-3.5" />
              Priority
            </button>
          </Dropdown>

          <!-- Due Date -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('date')"
            >
              <LucideCalendar class="h-3.5 w-3.5" />
              Due
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
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
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

          <!-- Copy to project -->
          <div class="relative">
            <Tooltip text="Copy to another project in the same team">
              <button
                type="button"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-ink-gray-7 transition hover:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Copy selected tasks to project"
                :disabled="!canCopySelectionToProject"
                @click.stop="togglePopover('copy-project')"
              >
                <LucideCopy class="h-4 w-4" />
              </button>
            </Tooltip>
            <div
              v-if="activePopover === 'copy-project'"
              class="absolute w-64 p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <Autocomplete
                :options="copyProjectOptions"
                placeholder="Copy to project..."
                @update:modelValue="bulkCopyToProject"
              />
              <div v-if="!copyProjectOptions.length" class="px-2 py-1 text-sm text-ink-gray-5">
                No other project in this team
              </div>
            </div>
          </div>

          <div class="w-px h-4 bg-outline-gray-2"></div>

          <!-- Delete -->
          <Tooltip text="Delete selected tasks">
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-lg text-red-500 transition hover:bg-surface-red-1"
              aria-label="Delete selected tasks"
              @click="confirmBulkDelete"
            >
              <LucideTrash2 class="h-4 w-4" />
            </button>
          </Tooltip>

          <!-- Clear -->
          <Tooltip text="Clear selection">
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-lg text-ink-gray-5 transition hover:bg-surface-gray-2 hover:text-ink-gray-7"
              aria-label="Clear selection"
              @click="clearSelection"
            >
              <LucideX class="h-4 w-4" />
            </button>
          </Tooltip>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
<script>
import { h } from 'vue'
import { Dropdown, Autocomplete, Tooltip, call } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import ListView from './ListView.vue'
import KanbanView from './KanbanView.vue'
import TeamView from './TeamView.vue'
import { activeProjects } from '@/data/projects'
import { activeUsers } from '@/data/users'

const COLUMNS_STORAGE_KEY = 'gameplan_task_columns'
const TASK_TYPES = [
  'Task',
  'Feature',
  'Milestone',
  'Improvement',
  'Bug',
  'Event',
  'Form Response',
  'Meeting Note',
  'Request',
  'Approval',
  'Follow-up',
  'Documentation',
  'Support',
]

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
      showFiltersPanel: false,
      filtersPanelStyle: {},
      openFilterValueMenu: null,
      showAddFilterMenu: false,
      inlinePopover: { name: null, field: null },
      selectedTag: null,
      allTags: [],
      taskFilters: [],
      nextFilterId: 1,
      dateFilterFields: ['due_date', 'creation'],
      filterFields: [
        { label: 'Status', value: 'status' },
        { label: 'Tags', value: 'tag' },
        { label: 'Due Date', value: 'due_date' },
        { label: 'Priority', value: 'priority' },
        { label: 'Assignee', value: 'assignee' },
        { label: 'Type', value: 'task_type' },
        { label: 'Project', value: 'project' },
        { label: 'Created By', value: 'owner' },
        { label: 'Date Created', value: 'creation' },
      ],
      filterOperators: [
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not_equals' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not_like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not_in' },
        { label: 'Is', value: 'is' },
      ],
      columns: {
        assignee:   { label: 'Assignee',    visible: saved.assignee   ?? true },
        priority:   { label: 'Priority',    visible: saved.priority   ?? true },
        due_date:   { label: 'Due Date',    visible: saved.due_date   ?? true },
        status:     { label: 'Status',      visible: saved.status     ?? false },
        modified:   { label: 'Modified',    visible: saved.modified   ?? true },
        created_by: { label: 'Created By',  visible: saved.created_by ?? false },
        tags:       { label: 'Tags',        visible: saved.tags       ?? true },
      },
    }
  },
  watch: {
    selectedTag() {
      this.$resources.tasks.reload()
    },
  },
  mounted() {
    document.addEventListener('click', this.handleOutsideClick)
    call('gameplan.gameplan.doctype.gp_task.gp_task.get_task_tags', { txt: '' }).then((tags) => {
      this.allTags = tags || []
    })
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
        fields: ['*', '_user_tags', 'project.title as project_title', 'team.title as team_title'],
        filters: { ...this.listOptions.filters, ...(this.selectedTag ? { tag: this.selectedTag } : {}) },
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
      if (this.showFiltersPanel) {
        this.showFiltersPanel = false
      }
      if (this.openFilterValueMenu) {
        this.openFilterValueMenu = null
      }
      if (this.showAddFilterMenu) {
        this.showAddFilterMenu = false
      }
      if (this.inlinePopover.name) {
        this.inlinePopover = { name: null, field: null }
      }
    },
    toggleFiltersPanel(event) {
      if (!this.showFiltersPanel && event?.currentTarget) {
        const rect = event.currentTarget.getBoundingClientRect()
        this.filtersPanelStyle = {
          top: `${rect.bottom + 8}px`,
          right: `${Math.max(window.innerWidth - rect.right, 16)}px`,
        }
      }
      this.showFiltersPanel = !this.showFiltersPanel
      if (!this.showFiltersPanel) {
        this.openFilterValueMenu = null
      }
    },
    toggleAddFilterMenu() {
      this.showAddFilterMenu = !this.showAddFilterMenu
    },
    addTaskFilterForField(field) {
      this.taskFilters.push({
        id: this.nextFilterId++,
        field,
        operator: 'equals',
        value: '',
        values: [],
      })
      this.showAddFilterMenu = false
    },
    removeTaskFilter(id) {
      this.taskFilters = this.taskFilters.filter((filter) => filter.id !== id)
      if (this.openFilterValueMenu === id) {
        this.openFilterValueMenu = null
      }
    },
    clearAllFilters() {
      this.taskFilters = []
      this.selectedTag = null
      this.openFilterValueMenu = null
      this.showAddFilterMenu = false
    },
    resetFilterValue(filter) {
      if (!this.operatorsForFilter(filter).some((operator) => operator.value === filter.operator)) {
        filter.operator = 'equals'
      }
      filter.value = ''
      filter.values = []
      if (!this.filterNeedsValue(filter)) {
        filter.value = ''
      }
    },
    operatorsForFilter(filter) {
      if (this.dateFilterFields.includes(filter.field)) {
        return this.filterOperators.filter((operator) => ['equals', 'not_equals', 'in', 'not_in', 'is'].includes(operator.value))
      }
      return this.filterOperators
    },
    filterNeedsValue(filter) {
      return filter.operator !== 'is'
    },
    isMultiValueFilter(filter) {
      return ['in', 'not_in'].includes(filter.operator)
    },
    isLikeFilter(filter) {
      return ['like', 'not_like'].includes(filter.operator)
    },
    toggleFilterValueMenu(id) {
      this.openFilterValueMenu = this.openFilterValueMenu === id ? null : id
    },
    toggleFilterValue(filter, value) {
      if (!Array.isArray(filter.values)) {
        filter.values = []
      }
      if (filter.values.includes(value)) {
        filter.values = filter.values.filter((item) => item !== value)
      } else {
        filter.values = [...filter.values, value]
      }
    },
    selectedFilterValueLabel(filter) {
      if (!Array.isArray(filter.values) || !filter.values.length) return ''
      const labelsByValue = new Map(this.valueOptionsForFilter(filter).map((option) => [option.value, option.label]))
      const labels = filter.values.map((value) => labelsByValue.get(value) || value)
      if (labels.length <= 2) return labels.join(', ')
      return `${labels.slice(0, 2).join(', ')} +${labels.length - 2}`
    },
    valueOptionsForFilter(filter) {
      const options = {
        status: ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Reopen'].map((value) => ({ label: value, value })),
        priority: ['Urgent', 'High', 'Medium', 'Low'].map((value) => ({ label: value, value })),
        task_type: TASK_TYPES.map((value) => ({ label: value, value })),
        tag: this.allTags.map((value) => ({ label: value, value })),
        assignee: this.userOptions,
        owner: this.userOptions,
        project: this.projectOptions,
      }
      return options[filter.field] || []
    },
    taskValueForFilter(task, field) {
      if (field === 'assignee') return this.assigneeIds(task)
      if (field === 'tag') return this.parseTags(task._user_tags)
      return task[field]
    },
    taskMatchesFilter(task, filter) {
      if (!filter.field || !filter.operator) return true
      const rawValue = this.taskValueForFilter(task, filter.field)
      const hasValue = Array.isArray(rawValue)
        ? rawValue.length > 0
        : rawValue !== null && rawValue !== undefined && String(rawValue).trim() !== ''

      if (filter.operator === 'is') return hasValue
      const expectedList = this.expectedValuesForFilter(filter)
      if (!this.filterNeedsValue(filter) || !expectedList.length) return true

      const expected = expectedList[0] || ''
      const values = Array.isArray(rawValue)
        ? rawValue.map((value) => String(value).toLowerCase())
        : [String(rawValue || '').toLowerCase()]

      if (this.dateFilterFields.includes(filter.field)) {
        const actualDate = rawValue ? this.$dayjs(rawValue).startOf('day') : null
        const expectedDate = this.$dayjs(filter.value).startOf('day')
        if (!actualDate?.isValid?.() || !expectedDate.isValid()) return true
        if (filter.operator === 'equals') return actualDate.isSame(expectedDate)
        if (filter.operator === 'not_equals') return !actualDate.isSame(expectedDate)
        if (filter.operator === 'in') return expectedList.some((value) => actualDate.isSame(this.$dayjs(value).startOf('day')))
        if (filter.operator === 'not_in') return expectedList.every((value) => !actualDate.isSame(this.$dayjs(value).startOf('day')))
      }

      if (filter.operator === 'equals') return values.includes(expected)
      if (filter.operator === 'not_equals') return !values.includes(expected)
      if (filter.operator === 'like') return values.some((value) => value.includes(expected))
      if (filter.operator === 'not_like') return values.every((value) => !value.includes(expected))
      if (filter.operator === 'in') return values.some((value) => expectedList.includes(value))
      if (filter.operator === 'not_in') return values.every((value) => !expectedList.includes(value))
      return true
    },
    expectedValuesForFilter(filter) {
      if (this.isMultiValueFilter(filter) && Array.isArray(filter.values) && filter.values.length) {
        return filter.values.map((value) => String(value).trim().toLowerCase()).filter(Boolean)
      }
      return String(filter.value || '')
        .split(',')
        .map((value) => value.trim().toLowerCase())
        .filter(Boolean)
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
    removeAssignee(task, user) {
      const remaining = this.assigneeIds(task).filter((id) => id !== user)
      this.inlinePopover = { name: null, field: null }
      this.tasks.setValue.submit({
        name: task.name,
        assignees: remaining.map((user) => ({ user })),
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
      if (name === 'copy-project' && !this.canCopySelectionToProject) {
        this.$dialog({
          title: 'Cannot copy selection',
          message: 'Select tasks from one team to copy them to another project in that same team.',
        })
        return
      }
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
    async bulkCopyToProject(option) {
      if (!option) return
      this.activePopover = null
      for (const task of this.selectedTaskDocs) {
        await call('frappe.client.insert', {
          doc: {
            doctype: 'GP Task',
            title: task.title,
            description: task.description,
            start_date: task.start_date || null,
            due_date: task.due_date || null,
            task_type: task.task_type || 'Task',
            status: task.status || 'Backlog',
            priority: task.priority || null,
            project: option.value,
            team: this.copyTargetTeam,
            assignees: this.assigneeIds(task).map((user) => ({ user })),
          },
        })
      }
      this.clearSelection()
      this.tasks.reload()
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
    assigneeHeatClass(user) {
      return 'text-white shadow-sm'
    },
    assigneeHeatStyle(user) {
      const seed = `${this.$user(user).full_name || ''}:${user || ''}`
      const palette = [
        { bg: '#b91c1c', ring: '#7f1d1d' },
        { bg: '#c2410c', ring: '#7c2d12' },
        { bg: '#a16207', ring: '#713f12' },
        { bg: '#15803d', ring: '#14532d' },
        { bg: '#047857', ring: '#064e3b' },
        { bg: '#0369a1', ring: '#0c4a6e' },
        { bg: '#1d4ed8', ring: '#1e3a8a' },
        { bg: '#4338ca', ring: '#312e81' },
        { bg: '#7e22ce', ring: '#581c87' },
        { bg: '#be185d', ring: '#831843' },
      ]
      const color = palette[this.hashStringToIndex(seed, palette.length)]
      return {
        backgroundColor: color.bg,
        borderColor: '#fff',
        '--tw-ring-color': color.ring,
      }
    },
    hashStringToIndex(value, length) {
      let hash = 0
      for (let i = 0; i < value.length; i++) {
        hash = (hash << 5) - hash + value.charCodeAt(i)
        hash |= 0
      }
      return Math.abs(hash) % length
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
    parseTags(tags) {
      if (!tags) return []
      return String(tags)
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean)
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
    activeFilterCount() {
      return this.taskFilters.filter((filter) => {
        return !this.filterNeedsValue(filter) || this.expectedValuesForFilter(filter).length
      }).length + (this.selectedTag ? 1 : 0)
    },
    filteredTasks() {
      return (this.tasks.data || []).filter((task) => {
        return this.taskFilters.every((filter) => this.taskMatchesFilter(task, filter))
      })
    },
    projectOptions() {
      return activeProjects.value.map((p) => ({
        label: p.title,
        value: p.name,
      }))
    },
    selectedTaskTeams() {
      const teams = new Set()
      for (const task of this.selectedTaskDocs) {
        const project = activeProjects.value.find((p) => p.name === task.project)
        const team = task.team || project?.team
        if (team) teams.add(team)
      }
      return [...teams]
    },
    selectedTaskProjectNames() {
      return new Set(this.selectedTaskDocs.map((task) => task.project).filter(Boolean))
    },
    canCopySelectionToProject() {
      return this.selectedTaskDocs.length > 0 && this.selectedTaskTeams.length === 1
    },
    copyTargetTeam() {
      return this.selectedTaskTeams[0] || null
    },
    copyProjectOptions() {
      if (!this.canCopySelectionToProject) return []
      return activeProjects.value
        .filter((project) => {
          return (
            project.team === this.copyTargetTeam &&
            !this.selectedTaskProjectNames.has(project.name)
          )
        })
        .map((project) => ({
          label: project.title,
          value: project.name,
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
    filterOptions() {
      const tagOptions = this.allTags.map((tag) => ({
        label: this.selectedTag === tag ? `${tag} selected` : tag,
        onClick: () => {
          this.selectedTag = this.selectedTag === tag ? null : tag
        },
      }))

      if (this.selectedTag) {
        return [
          { label: 'Clear tag filter', onClick: () => (this.selectedTag = null) },
          ...tagOptions,
        ]
      }

      return tagOptions
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
      return this.filteredTasks.reduce((childrenByParent, task) => {
        if (!task.parent_task) return childrenByParent
        if (!childrenByParent[task.parent_task]) {
          childrenByParent[task.parent_task] = []
        }
        childrenByParent[task.parent_task].push(task)
        return childrenByParent
      }, {})
    },
    topLevelTasks() {
      return this.filteredTasks.filter((task) => !task.parent_task)
    },
  },
}
</script>
