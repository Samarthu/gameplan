<template>
  <div>
    <div class="@container overflow-x-auto" v-if="tasksResource.data?.length" @scroll.passive="syncGroupHeaderScroll">
      <!-- Column header row — scrolls horizontally with columns -->
      <div v-if="!compact" class="sticky top-0 z-[3] flex min-w-full items-center border-b border-outline-gray-2 bg-surface-white px-1 py-1.5 text-xs font-medium text-ink-gray-5">
        <div class="sticky left-0 z-[1] flex min-w-[21rem] flex-1 items-center bg-surface-white">
          <div class="w-9 shrink-0"></div>
          <div class="w-7 shrink-0"></div>
          <div class="w-4 shrink-0"></div>
          <div class="flex-1 pl-1">Task</div>
        </div>
        <div class="w-32 shrink-0 pl-2">Type</div>
        <div v-if="columns.assignee.visible" class="w-28 shrink-0 text-center">Assignee</div>
        <div v-if="columns.priority.visible" class="w-24 shrink-0 pl-2">Priority</div>
        <div v-if="columns.due_date.visible" class="w-24 shrink-0 pl-2">Due Date</div>
        <div v-if="columns.status.visible" class="w-40 shrink-0 pl-2">Status</div>
        <div v-if="columns.tags.visible" class="w-40 shrink-0 pl-2">Tags</div>
        <div v-if="columns.modified.visible" class="w-24 shrink-0 pr-2 text-right">Modified</div>
        <div v-if="columns.created_by.visible" class="w-28 shrink-0 pl-2">Created By</div>
        <div class="relative flex w-8 shrink-0 items-center justify-end pr-1" >
          <Tooltip text="Manage columns">
            <button
              class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-7 focus:outline-none"
              @click.stop="toggleColumnsPicker($event)"
            >
              <LucideSlidersHorizontal class="h-3.5 w-3.5" />
            </button>
          </Tooltip>
        </div>
      </div>

      <!-- Groups — each group title is a direct child of the scroll container
           so width:100% = visible viewport width, making sticky left-0 work -->
      <div v-for="group in groupedTasks" :key="group.title">
        <!-- Group title: outside min-w-max so it sticks at left:0 correctly -->
        <button
          class="task-group-header group sticky z-[2] flex items-baseline rounded-sm bg-surface-menu-bar px-2.5 py-2 text-base transition-colors hover:bg-surface-gray-2"
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
        <div class="min-w-full" :class="{ hidden: !(isOpen[group.title] ?? true) }">
          <div v-for="(d, index) in visibleTasksForGroup(group.tasks)" :key="d.name">
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
              :class="[
                isSelected(d.name)
                  ? 'bg-surface-blue-1'
                  : d.parent_task
                    ? 'bg-surface-gray-1 hover:bg-surface-gray-2'
                    : 'hover:bg-surface-gray-2',
                d.parent_task ? 'border-l-2 border-outline-gray-3' : '',
              ]"
              @click="$router.push(taskRoute(d))"
            >
              <!-- Sticky Task column: checkbox + status + child indicator + title -->
              <div class="sticky left-0 z-[1] flex min-w-[21rem] flex-1 items-center"
                :class="[
                  isSelected(d.name)
                    ? 'bg-surface-blue-1'
                    : d.parent_task
                      ? 'bg-surface-gray-1 group-hover:bg-surface-gray-2'
                      : 'bg-surface-white group-hover:bg-surface-gray-2',
                ]"
                :style="{ paddingLeft: `${taskDepth(d) * 1}rem` }"
              >
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
                    v-if="tasksResource.delete.loading && tasksResource.delete.params.name === d.name"
                  />
                  <Tooltip text="Change status" v-else>
                    <Dropdown
                      :options="statusOptions({ onClick: (status) => tasksResource.setValue.submit({ status, name: d.name }) })"
                    >
                      <button class="flex rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3">
                        <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" />
                      </button>
                    </Dropdown>
                  </Tooltip>
                </div>

                <!-- Child task indicator -->
                <div class="flex w-4 shrink-0 items-center justify-center">
                  <button
                    v-if="hasChildTasks(d)"
                    class="rounded p-0.5 text-ink-gray-4 hover:bg-surface-gray-3 hover:text-ink-gray-7 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                    @click.stop="toggleChildTasks(d.name)"
                  >
                    <LucideChevronDown
                      v-if="isChildTasksOpen(d.name)"
                      class="h-3 w-3"
                    />
                    <LucideChevronRight
                      v-else
                      class="h-3 w-3"
                    />
                  </button>
                  <LucideCornerDownRight
                    v-else-if="d.parent_task"
                    class="h-3 w-3 text-ink-gray-3"
                  />
                </div>

                <!-- Title + ID -->
                <router-link
                  :to="taskRoute(d)"
                  class="flex min-h-[2.5rem] min-w-0 flex-1 items-center py-2 pr-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                  :class="{ 'pointer-events-none': tasksResource.delete.loading && tasksResource.delete.params.name === d.name }"
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

              <div class="flex w-32 shrink-0 items-center py-2 pl-2">
                <div @click.stop>
                  <Dropdown :options="taskTypeOptions({ onClick: (task_type) => tasksResource.setValue.submit({ task_type, name: d.name }) })">
                    <button class="flex max-w-full items-center gap-1 rounded px-1 py-0.5 hover:bg-surface-gray-3 focus:outline-none">
                      <LucideCircle class="h-3 w-3 shrink-0 text-ink-gray-5" />
                      <span class="truncate text-sm text-ink-gray-7">{{ d.task_type || 'Task' }}</span>
                    </button>
                  </Dropdown>
                </div>
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
                          class="group/assignee relative inline-grid h-6 w-6 place-items-center rounded-full border-2 border-white text-sm font-medium shadow-sm ring-1"
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
                            v-if="assigneeIds(d).length > 1"
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
                class="flex w-40 shrink-0 items-center py-2 pl-2"
              >
                <div @click.stop>
                  <Dropdown :options="statusOptions({ onClick: (status) => tasksResource.setValue.submit({ status, name: d.name }) })">
                    <button class="flex max-w-full items-center gap-2 whitespace-nowrap rounded px-1 py-0.5 hover:bg-surface-gray-3 focus:outline-none">
                      <TaskStatusIcon :status="d.status" :overdue="isTaskOverdue(d)" class="shrink-0" />
                      <span class="truncate text-sm text-ink-gray-7">{{ d.status || '—' }}</span>
                    </button>
                  </Dropdown>
                </div>
              </div>

              <!-- Tags column -->
              <div v-if="columns.tags.visible" class="flex w-40 shrink-0 items-center gap-1 py-2 pl-2">
                <template v-if="parseTags(d._user_tags).length">
                  <span
                    v-for="tag in parseTags(d._user_tags).slice(0, 2)"
                    :key="tag"
                    class="inline-flex shrink-0 items-center gap-1 rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700"
                  >
                    <LucideTag class="h-3 w-3 shrink-0" />
                    {{ tag }}
                  </span>
                  <Tooltip v-if="parseTags(d._user_tags).length > 2" :text="parseTags(d._user_tags).slice(2).join(', ')">
                    <span class="shrink-0 rounded bg-surface-gray-3 px-1.5 py-0.5 text-xs text-ink-gray-6">
                      +{{ parseTags(d._user_tags).length - 2 }}
                    </span>
                  </Tooltip>
                </template>
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

              <!-- Row actions -->
              <div class="flex w-20 shrink-0 items-center justify-end gap-1 pr-1 py-2">
                <!-- Set Sprint -->
                <div class="relative">
                  <Tooltip text="Set Sprint">
                    <button
                      class="invisible grid h-6 w-6 shrink-0 place-items-center rounded text-ink-gray-4 hover:bg-surface-gray-2 hover:text-ink-gray-7 focus:visible focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 group-hover:visible"
                      @click.stop="toggleInlinePopover(d.name, 'sprint')"
                    >
                      <LucideZap class="h-3.5 w-3.5" />
                    </button>
                  </Tooltip>
                  <div
                    v-if="inlinePopover.name === d.name && inlinePopover.field === 'sprint'"
                    class="absolute right-0 top-full z-50 mt-1 w-56 rounded-lg border border-outline-gray-2 bg-surface-white p-2 shadow-lg"
                    @click.stop
                  >
                    <Autocomplete
                      :options="sprintOptions"
                      placeholder="Assign sprint..."
                      @update:modelValue="(opt) => { if (opt) { tasksResource.setValue.submit({ name: d.name, sprint: opt.value }); toggleInlinePopover(d.name, 'sprint') } }"
                    />
                    <button
                      v-if="d.sprint"
                      class="mt-1 w-full rounded px-2 py-1 text-left text-xs text-ink-gray-5 hover:bg-surface-gray-2"
                      @click.stop="tasksResource.setValue.submit({ name: d.name, sprint: null }); toggleInlinePopover(d.name, 'sprint')"
                    >
                      Remove from sprint
                    </button>
                  </div>
                </div>
                <Tooltip text="Delete task" v-if="canDeleteTask(d)">
                  <button
                    class="invisible grid h-6 w-6 shrink-0 place-items-center rounded text-ink-gray-4 hover:bg-surface-red-1 hover:text-red-500 focus:visible focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 group-hover:visible"
                    :disabled="tasksResource.delete.loading && tasksResource.delete.params.name === d.name"
                    @click.stop="confirmDeleteTask(d)"
                  >
                    <LucideTrash2 class="h-3.5 w-3.5" />
                  </button>
                </Tooltip>
              </div>
            </div>
            <div class="mx-2.5 border-b" v-if="index < visibleTasksForGroup(group.tasks).length - 1"></div>
          </div>
        </div><!-- end min-w-max per group -->
      </div>
    </div>


  </div>
  <Teleport to="body">
    <div
      v-if="showColumnsPicker"
      class="fixed z-50 w-44 rounded-lg border border-outline-gray-2 bg-surface-white py-1 shadow-lg"
      :style="columnsPickerStyle"
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
  </Teleport>
</template>

<script>
import { LoadingIndicator, Dropdown, Tooltip, Autocomplete } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import UserAvatar from './UserAvatar.vue'
import LucideX from '~icons/lucide/x'
import { sprints } from '@/data/sprints'

export default {
  name: 'ListView',
  components: {
    LoadingIndicator,
    Dropdown,
    Tooltip,
    Autocomplete,
    TaskStatusIcon,
    UserAvatar,
    LucideX,
  },
  props: {
    tasksResource: { type: Object, required: true },
    groupedTasks: { type: Array, required: true },
    compact: { type: Boolean, default: false },
    columns: { type: Object, required: true },
    isOpen: { type: Object, required: true },
    horizontalScrollLeft: { type: Number, default: 0 },
    showColumnsPicker: { type: Boolean, default: false },
    columnsPickerStyle: { type: Object, default: () => ({}) },
    inlinePopover: { type: Object, required: true },
    userOptions: { type: Array, required: true },
    syncGroupHeaderScroll: { type: Function, required: true },
    visibleTasksForGroup: { type: Function, required: true },
    isGroupFullySelected: { type: Function, required: true },
    isGroupPartiallySelected: { type: Function, required: true },
    toggleGroup: { type: Function, required: true },
    isSelected: { type: Function, required: true },
    toggleTask: { type: Function, required: true },
    taskRoute: { type: Function, required: true },
    isTaskOverdue: { type: Function, required: true },
    statusOptions: { type: Function, required: true },
    taskTypeOptions: { type: Function, required: true },
    hasChildTasks: { type: Function, required: true },
    isChildTasksOpen: { type: Function, required: true },
    toggleChildTasks: { type: Function, required: true },
    taskDepth: { type: Function, required: true },
    assigneeIds: { type: Function, required: true },
    assigneeStackSpacingClass: { type: Function, required: true },
    visibleAssigneeIds: { type: Function, required: true },
    assigneeHeatClass: { type: Function, required: true },
    assigneeHeatStyle: { type: Function, required: true },
    extraAssigneeCount: { type: Function, required: true },
    extraAssigneeNames: { type: Function, required: true },
    toggleInlinePopover: { type: Function, required: true },
    setAssignee: { type: Function, required: true },
    removeAssignee: { type: Function, required: true },
    priorityOptions: { type: Function, required: true },
    setDueDate: { type: Function, required: true },
    canDeleteTask: { type: Function, required: true },
    confirmDeleteTask: { type: Function, required: true },
    toggleColumn: { type: Function, required: true },
    toggleColumnsPicker: { type: Function, required: true },
  },
  computed: {
    sprintOptions() {
      return (sprints.data || []).map((s) => ({ label: s.title, value: s.name }))
    },
  },
  methods: {
    userInitial(user) {
      const fullName = this.$user(user).full_name || user || ''
      return fullName.trim().charAt(0).toUpperCase()
    },
    parseTags(raw) {
      if (!raw) return []
      return raw.split(',').map((t) => t.trim()).filter(Boolean)
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
