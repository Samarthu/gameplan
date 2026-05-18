<template>
  <div>
    <div class="@container overflow-x-auto" v-if="tasks.data?.length" @scroll.passive="syncGroupHeaderScroll">
      <!-- Column header row — scrolls horizontally with columns -->
      <div v-if="!compact" class="min-w-max sticky top-0 z-30 flex items-center border-b border-outline-gray-2 bg-surface-white px-1 py-1.5 text-xs font-medium text-ink-gray-5">
        <div class="sticky left-0 z-10 flex w-[21rem] shrink-0 items-center bg-surface-white">
          <div class="w-9 shrink-0"></div>
          <div class="w-7 shrink-0"></div>
          <div class="w-4 shrink-0"></div>
          <div class="flex-1 pl-1">Task</div>
        </div>
        <div v-if="columns.assignee.visible" class="w-28 shrink-0 text-center">Assignee</div>
        <div v-if="columns.priority.visible" class="w-24 shrink-0 pl-2">Priority</div>
        <div v-if="columns.due_date.visible" class="w-24 shrink-0 pl-2">Due Date</div>
        <div v-if="columns.status.visible" class="w-28 shrink-0 pl-2">Status</div>
        <div v-if="columns.modified.visible" class="w-24 shrink-0 pr-2 text-right">Modified</div>
        <div v-if="columns.created_by.visible" class="w-28 shrink-0 pl-2">Created By</div>
        <div class="relative flex w-10 shrink-0 items-center justify-end pr-1" ref="columnsPicker">
          <Tooltip text="Manage columns">
            <button
              class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-7 focus:outline-none"
              @click.stop="showColumnsPicker = !showColumnsPicker"
            >
              <LucideSlidersHorizontal class="h-3.5 w-3.5" />
            </button>
          </Tooltip>
          <div
            v-if="showColumnsPicker"
            class="absolute right-0 top-full z-50 mt-1 w-44 rounded-lg border border-outline-gray-2 bg-surface-white py-1 shadow-lg"
            @click.stop
          >
            <div class="border-b border-outline-gray-2 px-3 py-1.5 text-xs font-semibold text-ink-gray-5">
              Columns
            </div>
            <button
              v-for="(col, key) in columns"
              :key="key"
              class="flex w-full items-center gap-2.5 px-3 py-1.5 text-sm text-ink-gray-8 hover:bg-surface-gray-2"
              @click="toggleColumn(key)"
            >
              <span
                class="flex h-4 w-4 shrink-0 items-center justify-center rounded border"
                :class="col.visible ? 'border-ink-gray-9 bg-ink-gray-9' : 'border-outline-gray-3 bg-surface-white'"
              >
                <LucideCheck v-if="col.visible" class="h-3 w-3 text-surface-white" />
              </span>
              {{ col.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Groups — each group title is a direct child of the scroll container
           so width:100% = visible viewport width, making sticky left-0 work -->
      <div v-for="group in groupedTasks" :key="group.title">
        <!-- Group title: outside min-w-max so it sticks at left:0 correctly -->
        <button
          class="task-group-header group sticky z-20 flex items-baseline rounded-sm bg-surface-menu-bar px-2.5 py-2 text-base transition-colors hover:bg-surface-gray-2"
          :class="compact ? 'top-0' : 'top-[2.125rem]'"
          :style="{ transform: `translateX(${horizontalScrollLeft}px)` }"
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
          <span class="font-medium text-ink-gray-9">{{ group.title }}</span>
          <span class="ml-2 text-sm text-ink-gray-5">{{ group.tasks.length }}</span>
          <span class="ml-auto hidden text-sm text-ink-gray-5 group-hover:inline">
            {{ isOpen[group.title] ? 'Collapse' : 'Expand' }}
          </span>
        </button>
        <!-- Task rows: inside min-w-max for horizontal scroll -->
        <div class="min-w-max" :class="{ hidden: !(isOpen[group.title] ?? true) }">
          <div v-for="(d, index) in group.tasks" :key="d.name">
            <!-- ── Compact card row (overview widgets) ── -->
            <div
              v-if="compact"
              class="flex cursor-pointer items-center gap-3 rounded px-2 py-2.5 transition"
              :class="isSelected(d.name) ? 'bg-surface-blue-1' : 'hover:bg-surface-gray-2'"
              @click="$router.push(taskRoute(d))"
            >
              <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" class="shrink-0" />
              <div class="min-w-0 flex-1">
                <div class="flex items-baseline justify-between gap-2">
                  <span class="overflow-hidden text-ellipsis whitespace-nowrap text-base font-medium text-ink-gray-9">
                    {{ d.title }}
                  </span>
                  <span class="shrink-0 whitespace-nowrap text-sm text-ink-gray-4">
                    {{ $dayjs(d.modified).fromNow() }}
                  </span>
                </div>
                <div class="mt-0.5 flex items-center justify-between text-sm text-ink-gray-4">
                  <span>#{{ d.name }}</span>
                  <div
                    class="inline-grid h-4 w-4 place-items-center rounded-full bg-surface-gray-3 text-xs"
                    :class="[d.unread ? 'text-ink-gray-9' : 'text-ink-gray-5', d.comments_count ? '' : 'invisible']"
                  >
                    {{ d.comments_count || 0 }}
                  </div>
                </div>
              </div>
            </div>

            <!-- ── Full table row (tasks page) ── -->
            <div
              v-else
              class="group flex cursor-pointer items-center rounded transition"
              :class="isSelected(d.name) ? 'bg-surface-blue-1' : 'hover:bg-surface-gray-2'"
              @click="$router.push(taskRoute(d))"
            >
              <!-- Sticky Task column: checkbox + status + child indicator + title -->
              <div class="sticky left-0 z-10 flex w-[21rem] shrink-0 items-center"
                :class="isSelected(d.name) ? 'bg-surface-blue-1' : 'bg-surface-white group-hover:bg-surface-gray-2'">
                <!-- Checkbox -->
                <label class="flex w-9 shrink-0 cursor-pointer items-center justify-center py-2" @click.stop>
                  <input
                    type="checkbox"
                    class="h-4 w-4 cursor-pointer rounded border-gray-300 accent-gray-800 focus:ring-0"
                    :checked="isSelected(d.name)"
                    @change="toggleTask(d.name)"
                  />
                </label>

                <!-- Status icon -->
                <div class="flex w-7 shrink-0 items-center justify-center py-2" @click.stop>
                  <LoadingIndicator
                    class="h-4 w-4 text-ink-gray-5"
                    v-if="tasks.delete.loading && tasks.delete.params.name === d.name"
                  />
                  <Tooltip text="Change status" v-else>
                    <Dropdown
                      :options="statusOptions({ onClick: (status) => tasks.setValue.submit({ status, name: d.name }) })"
                    >
                      <button class="flex rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3">
                        <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" />
                      </button>
                    </Dropdown>
                  </Tooltip>
                </div>

                <!-- Child task indicator -->
                <div class="flex w-4 shrink-0 items-center justify-center">
                  <LucideCornerDownRight
                    v-if="d.parent_task"
                    class="h-3 w-3 text-ink-gray-3"
                  />
                </div>

                <!-- Title + ID -->
                <router-link
                  :to="taskRoute(d)"
                  class="flex min-h-[2.5rem] min-w-0 flex-1 items-center py-2 pr-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                  :class="{ 'pointer-events-none': tasks.delete.loading && tasks.delete.params.name === d.name }"
                  @click.stop
                >
                  <div class="flex min-w-0 items-baseline gap-2">
                    <div class="min-w-0 overflow-hidden text-ellipsis whitespace-nowrap text-base font-medium leading-4 text-ink-gray-9">
                      {{ d.title }}
                    </div>
                    <span class="shrink-0 text-sm text-ink-gray-5">#{{ d.name }}</span>
                  </div>
                </router-link>
              </div>

              <!-- Assignee column (inline edit) -->
              <div
                v-if="columns.assignee.visible"
                class="relative flex w-28 shrink-0 items-center justify-center py-2"
              >
                <button
                  class="flex items-center gap-1 rounded px-1 py-0.5 hover:bg-surface-gray-3 focus:outline-none"
                  @click.stop="toggleInlinePopover(d.name, 'assignee')"
                >
                  <template v-if="assigneeIds(d).length">
                    <div class="isolate flex items-center" :class="assigneeStackSpacingClass(d)">
                      <Tooltip
                        v-for="(uid, idx) in visibleAssigneeIds(d)"
                        :key="uid + '-' + idx"
                        :text="$user(uid).full_name"
                      >
                        <span
                          class="relative inline-flex rounded-full ring-2 ring-surface-white"
                          :style="{ zIndex: idx + 1 }"
                        >
                          <UserAvatar class="shrink-0" :user="uid" size="sm" />
                        </span>
                      </Tooltip>
                      <Tooltip v-if="extraAssigneeCount(d) > 0" :text="extraAssigneeNames(d)">
                        <span class="relative inline-flex h-5 min-w-[1.25rem] shrink-0 items-center justify-center rounded-full bg-surface-gray-3 px-1 text-xs font-medium text-ink-gray-8 ring-2 ring-surface-white">
                          +{{ extraAssigneeCount(d) }}
                        </span>
                      </Tooltip>
                    </div>
                  </template>
                  <span v-else class="text-sm text-ink-gray-3">—</span>
                </button>
                <!-- Assignee picker popover -->
                <div
                  v-if="inlinePopover.name === d.name && inlinePopover.field === 'assignee'"
                  class="absolute left-0 top-full z-50 mt-1 w-52 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-lg"
                  @click.stop
                >
                  <Autocomplete
                    :options="userOptions"
                    placeholder="Search user..."
                    @update:modelValue="(opt) => setAssignee(d, opt)"
                  />
                </div>
              </div>

              <!-- Priority column (inline edit) -->
              <div
                v-if="columns.priority.visible"
                class="flex w-24 shrink-0 items-center py-2 pl-2"
              >
                <div @click.stop>
                  <Dropdown :options="priorityOptions(d)">
                    <button class="flex items-center gap-1 rounded px-1 py-0.5 hover:bg-surface-gray-3 focus:outline-none">
                      <template v-if="d.priority">
                        <div
                          class="h-2 w-2 shrink-0 rounded-full"
                          :class="{
                            'bg-red-600': d.priority === 'Urgent',
                            'bg-surface-red-5': d.priority === 'High',
                            'bg-surface-amber-3': d.priority === 'Medium',
                            'bg-surface-gray-5': d.priority === 'Low',
                          }"
                        ></div>
                        <span class="ml-1 text-sm text-ink-gray-7">{{ d.priority }}</span>
                      </template>
                      <span v-else class="text-sm text-ink-gray-3">—</span>
                    </button>
                  </Dropdown>
                </div>
              </div>

              <!-- Due Date column (inline edit) -->
              <div
                v-if="columns.due_date.visible"
                class="relative flex w-24 shrink-0 items-center py-2 pl-2"
              >
                <button
                  class="flex items-center gap-1 rounded px-1 py-0.5 hover:bg-surface-gray-3 focus:outline-none"
                  @click.stop="toggleInlinePopover(d.name, 'due_date')"
                >
                  <template v-if="d.due_date">
                    <LucideCalendar
                      class="h-3 w-3 shrink-0"
                      :class="isTaskOverdue(d) ? 'text-red-500' : 'text-ink-gray-5'"
                    />
                    <span
                      class="ml-1 whitespace-nowrap text-sm"
                      :class="isTaskOverdue(d) ? 'text-red-500' : 'text-ink-gray-5'"
                    >
                      {{ $dayjs(d.due_date).format('D MMM') }}
                    </span>
                  </template>
                  <span v-else class="text-sm text-ink-gray-3">—</span>
                </button>
                <!-- Date picker popover -->
                <div
                  v-if="inlinePopover.name === d.name && inlinePopover.field === 'due_date'"
                  class="absolute left-0 top-full z-50 mt-1 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-lg"
                  @click.stop
                >
                  <input
                    type="date"
                    :value="d.due_date"
                    class="block rounded-md border border-outline-gray-2 px-2 py-1 text-sm text-ink-gray-9 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                    @change="setDueDate(d, $event.target.value)"
                  />
                  <button
                    v-if="d.due_date"
                    class="mt-1 w-full rounded px-2 py-1 text-xs text-ink-gray-5 hover:bg-surface-gray-2"
                    @click="setDueDate(d, '')"
                  >
                    Clear date
                  </button>
                </div>
              </div>

              <!-- Status text column (inline edit) -->
              <div
                v-if="columns.status.visible"
                class="flex w-28 shrink-0 items-center py-2 pl-2"
              >
                <div @click.stop>
                  <Dropdown :options="statusOptions({ onClick: (status) => tasks.setValue.submit({ status, name: d.name }) })">
                    <button class="flex items-center gap-1 rounded px-1 py-0.5 hover:bg-surface-gray-3 focus:outline-none">
                      <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" />
                      <span class="ml-1 text-sm text-ink-gray-7">{{ d.status || '—' }}</span>
                    </button>
                  </Dropdown>
                </div>
              </div>

              <!-- Modified column -->
              <div v-if="columns.modified.visible" class="w-24 shrink-0 py-2 pr-2 text-right">
                <span class="whitespace-nowrap text-sm text-ink-gray-5">{{ $dayjs(d.modified).fromNow() }}</span>
              </div>

              <!-- Created By column -->
              <div v-if="columns.created_by.visible" class="flex w-28 shrink-0 items-center justify-center py-2 pl-2">
                <Tooltip :text="$user(d.owner).full_name || d.owner">
                  <UserAvatar class="shrink-0" :user="d.owner" size="sm" />
                </Tooltip>
              </div>

              <!-- Comments count -->
              <div class="flex w-10 shrink-0 items-center justify-end pr-1 py-2">
                <div
                  class="inline-grid h-4 w-4 shrink-0 place-items-center rounded-full bg-surface-gray-3 text-xs"
                  :class="[d.unread ? 'text-ink-gray-9' : 'text-ink-gray-5', d.comments_count ? '' : 'invisible']"
                >
                  {{ d.comments_count || 0 }}
                </div>
              </div>
            </div>
            <div class="mx-2.5 border-b" v-if="index < group.tasks.length - 1"></div>
          </div>
        </div><!-- end min-w-max per group -->
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
            <button class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideCircleDot class="h-3.5 w-3.5" />
              Status
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
import { activeUsers } from '@/data/users'

const COLUMNS_STORAGE_KEY = 'gameplan_task_columns'

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
        Cancelled: false,
        Done: false,
      },
      selectedTasks: [],
      horizontalScrollLeft: 0,
      activePopover: null,
      showColumnsPicker: false,
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
    syncGroupHeaderScroll(event) {
      this.horizontalScrollLeft = event.target.scrollLeft
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
    toggleColumn(key) {
      this.columns[key].visible = !this.columns[key].visible
      const toSave = {}
      for (const [k, v] of Object.entries(this.columns)) toSave[k] = v.visible
      localStorage.setItem(COLUMNS_STORAGE_KEY, JSON.stringify(toSave))
    },
    handleOutsideClick(e) {
      if (this.showColumnsPicker && !this.$refs.columnsPicker?.contains(e.target)) {
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
    bulkStatusOptions() {
      return this.statusOptions({ onClick: (status) => this.bulkUpdate('status', status) })
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
        return [{ id: 'all', title: '', tasks: this.tasks.data }]
      }
      return ['In Progress', 'Under Testing', 'Ready to Merge', 'Todo', 'Backlog', 'Done', 'Cancelled', 'Reopen'].map((status) => {
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

<style scoped>
.task-group-header {
  width: 100%;
  min-width: 100%;
  max-width: 100%;
}

@supports (width: 100cqw) {
  .task-group-header {
    width: 100cqw;
    min-width: 100cqw;
    max-width: 100cqw;
  }
}
</style>
