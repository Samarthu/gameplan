<template>
  <div class="mt-8">
    <div class="mb-3 flex items-center justify-between">
      <h3 class="text-sm font-semibold text-ink-gray-7">
        Sub Tasks
        <span v-if="childTasks.data?.length" class="ml-1 text-ink-gray-4">
          {{ childTasks.data.length }}
        </span>
      </h3>
      <button
        class="flex items-center gap-1 rounded px-2 py-1 text-xs font-medium text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        @click="showAddForm = !showAddForm"
      >
        <LucidePlus class="h-3.5 w-3.5" />
        Add
      </button>
    </div>

    <!-- Add subtask inline form -->
    <div
      v-if="showAddForm"
      class="mb-2 flex items-center gap-2 rounded-lg border border-outline-gray-3 bg-surface-gray-1 px-3 py-2"
    >
      <input
        ref="newTitleInput"
        v-model="newTitle"
        type="text"
        placeholder="Subtask title..."
        class="flex-1 bg-transparent text-sm text-ink-gray-9 placeholder-ink-gray-3 focus:outline-none"
        @keydown.enter="addChildTask"
        @keydown.esc="cancelAdd"
      />
      <button
        class="rounded bg-ink-gray-9 px-2.5 py-1 text-xs font-medium text-surface-white hover:bg-ink-gray-7 disabled:opacity-50"
        :disabled="!newTitle.trim() || creating"
        @click="addChildTask"
      >
        {{ creating ? 'Adding…' : 'Add' }}
      </button>
      <button
        class="rounded px-2 py-1 text-xs text-ink-gray-5 hover:text-ink-gray-8"
        @click="cancelAdd"
      >
        Cancel
      </button>
    </div>

    <!-- Child task list -->
    <div v-if="childTasks.data?.length" class="space-y-px">
      <div
        v-for="task in childTasks.data"
        :key="task.name"
        class="group flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-surface-gray-2"
        @click="openTask(task)"
      >
        <!-- Status icon with change dropdown -->
        <div @click.stop>
          <Dropdown :options="statusOptionsFor(task)">
            <button class="flex shrink-0 focus:outline-none">
              <TaskStatusIcon :status="task.status" />
            </button>
          </Dropdown>
        </div>

        <!-- Title -->
        <span
          class="flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-sm text-ink-gray-8"
          :class="{ 'line-through text-ink-gray-4': task.status === 'Done' }"
        >
          {{ task.title }}
        </span>

        <!-- Assignee avatars -->
        <div v-if="assigneeIds(task).length" class="isolate flex shrink-0 items-center -space-x-1">
          <Tooltip
            v-for="(uid, idx) in assigneeIds(task).slice(0, 3)"
            :key="uid"
            :text="$user(uid).full_name"
          >
            <span
              class="relative inline-flex rounded-full ring-1 ring-surface-white"
              :style="{ zIndex: idx + 1 }"
            >
              <UserAvatar :user="uid" size="xs" />
            </span>
          </Tooltip>
        </div>

        <!-- Due date -->
        <span v-if="task.due_date" class="shrink-0 text-xs text-ink-gray-4">
          {{ $dayjs(task.due_date).format('D MMM') }}
        </span>

        <!-- Delete button -->
        <button
          v-if="canDeleteTask(task)"
          class="invisible shrink-0 rounded p-0.5 text-ink-gray-3 hover:text-red-500 group-hover:visible"
          @click.stop="deleteTask(task)"
        >
          <LucideX class="h-3.5 w-3.5" />
        </button>
      </div>
    </div>

    <div
      v-else-if="!showAddForm && !childTasks.loading"
      class="text-xs text-ink-gray-3"
    >
      No sub tasks yet. Click Add to create one.
    </div>
  </div>
</template>

<script>
import { createResource, Dropdown, Tooltip } from 'frappe-ui'
import { h } from 'vue'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import UserAvatar from './UserAvatar.vue'

export default {
  name: 'ChildTasks',
  props: {
    parentTaskId: { type: [String, Number], required: true },
    parentTask: { type: Object, default: null },
  },
  components: { Dropdown, Tooltip, TaskStatusIcon, UserAvatar },
  data() {
    return {
      showAddForm: false,
      newTitle: '',
      creating: false,
    }
  },
  resources: {
    childTasks() {
      return {
        type: 'list',
        url: 'gameplan.gameplan.doctype.gp_task.gp_task.get_list',
        cache: ['ChildTasks', this.parentTaskId],
        doctype: 'GP Task',
        fields: ['*', 'project.title as project_title', 'team.title as team_title'],
        filters: { parent_task: this.parentTaskId },
        orderBy: 'creation asc',
        auto: true,
        realtime: true,
      }
    },
    updateTask: {
      url: 'frappe.client.set_value',
    },
    deleteTaskResource: {
      url: 'frappe.client.delete',
    },
  },
  computed: {
    childTasks() {
      return this.$resources.childTasks
    },
  },
  methods: {
    async addChildTask() {
      const title = this.newTitle.trim()
      if (!title) return
      this.creating = true
      try {
        await createResource({ url: 'frappe.client.insert' }).submit({
          doc: {
            doctype: 'GP Task',
            title,
            parent_task: this.parentTaskId,
            project: this.parentTask?.project || null,
            team: this.parentTask?.team || null,
            status: 'Backlog',
          },
        })
        this.newTitle = ''
        this.showAddForm = false
        this.childTasks.reload()
      } finally {
        this.creating = false
      }
    },
    cancelAdd() {
      this.newTitle = ''
      this.showAddForm = false
    },
    openTask(task) {
      this.$router.push({
        name: task.project ? 'ProjectTaskDetail' : 'Task',
        params: { teamId: task.team, projectId: task.project, taskId: task.name },
      })
    },
    deleteTask(task) {
      this.$resources.deleteTaskResource.submit(
        { doctype: 'GP Task', name: task.name },
        { onSuccess: () => this.childTasks.reload() },
      )
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
    changeStatus(task, status) {
      this.$resources.updateTask.submit(
        { doctype: 'GP Task', name: task.name, fieldname: 'status', value: status },
        { onSuccess: () => this.childTasks.reload() },
      )
    },
    statusOptionsFor(task) {
      return ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Reopen', 'Brief Received', 'Ideation', 'Designing', 'Internal Review', 'Stakeholder Review', 'Revisions', 'Finalized', 'Design In Review', 'Design Confirmed', 'Hold', 'QA Accepted', 'Live'].map(
        (status) => ({
          icon: () => h(TaskStatusIcon, { status }),
          label: status,
          onClick: () => this.changeStatus(task, status),
        }),
      )
    },
    assigneeIds(task) {
      const rows = Array.isArray(task.assignees) ? task.assignees : []
      const fromRows = rows.map((r) => (typeof r === 'object' ? r.user : null)).filter(Boolean)
      if (fromRows.length) return fromRows
      return task.assigned_to ? [task.assigned_to] : []
    },
  },
  watch: {
    showAddForm(val) {
      if (val) {
        this.$nextTick(() => this.$refs.newTitleInput?.focus())
      }
    },
  },
}
</script>
