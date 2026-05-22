<template>
  <div class="w-full overflow-x-hidden pb-3">
    <div class="grid w-full grid-cols-[repeat(auto-fit,minmax(18rem,1fr))] gap-3">
      <section
        v-for="member in memberProgress"
        :key="member.id"
        class="flex max-h-[calc(100vh-12rem)] min-h-[26rem] flex-col rounded-md border border-outline-gray-2 bg-surface-white px-4 py-3 shadow-sm"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex min-w-0 items-center gap-2">
            <UserAvatar
              v-if="member.user"
              class="shrink-0"
              :user="member.user.name"
              size="sm"
            />
            <div
              v-else
              class="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-surface-gray-3 text-xs font-semibold text-ink-gray-6"
            >
              ?
            </div>
            <h3 class="truncate text-sm font-semibold text-ink-gray-8">{{ member.label }}</h3>
          </div>
          <button
            type="button"
            class="grid h-6 w-6 shrink-0 place-items-center rounded-md text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
            :aria-label="`Add task for ${member.label}`"
            @click="onAddTask(member)"
          >
            <LucidePlus class="h-4 w-4" />
          </button>
        </div>

        <div class="mt-5 grid grid-cols-[1fr_1fr_auto] items-center gap-3 text-sm">
          <div>
            <div class="font-semibold leading-5 text-ink-gray-8">{{ member.notDone }}</div>
            <div class="text-xs leading-4 text-ink-gray-5">Not done</div>
          </div>
          <div>
            <div class="font-semibold leading-5 text-ink-gray-8">{{ member.done }}</div>
            <div class="text-xs leading-4 text-ink-gray-5">Done</div>
          </div>
          <div class="relative grid h-14 w-14 place-items-center rounded-full">
            <svg class="absolute inset-0 h-14 w-14 -rotate-90" viewBox="0 0 36 36" aria-hidden="true">
              <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" stroke-width="3.5" class="text-gray-100" />
              <circle
                cx="18"
                cy="18"
                r="15.5"
                fill="none"
                stroke="currentColor"
                stroke-width="3.5"
                stroke-linecap="round"
                class="text-green-400"
                :stroke-dasharray="`${member.donePercent} ${100 - member.donePercent}`"
              />
            </svg>
            <span class="text-[11px] font-semibold leading-none text-ink-gray-6">{{ member.donePercent }}%</span>
          </div>
        </div>

        <div class="mt-3 flex h-1 overflow-hidden rounded-full bg-surface-gray-2">
          <div
            v-for="group in member.statusGroups"
            :key="group.status"
            class="h-full"
            :class="statusMeta(group.status).barClass"
            :style="{ width: `${member.total ? (group.tasks.length / member.total) * 100 : 0}%` }"
          ></div>
        </div>

        <div class="mt-5 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1 team-card-scroll">
          <div v-if="!member.tasks.length" class="rounded-md border border-dashed border-outline-gray-2 py-6 text-center text-sm text-ink-gray-5">
            No assigned tasks
          </div>
          <details
            v-for="group in member.statusGroups"
            :key="group.status"
            class="group"
          >
            <summary class="flex cursor-pointer list-none items-center gap-2 rounded px-1 py-1 text-xs font-semibold uppercase text-ink-gray-7 hover:bg-surface-gray-2">
              <LucideChevronRight class="h-3.5 w-3.5 text-ink-gray-4 transition group-open:rotate-90" />
              <span class="h-3 w-3 shrink-0 rounded-sm" :class="statusMeta(group.status).dotClass"></span>
              <span class="min-w-0 flex-1 truncate">{{ group.status || 'No Status' }}</span>
              <span class="text-xs font-medium text-ink-gray-5">({{ group.tasks.length }})</span>
            </summary>
            <div class="mt-1 divide-y divide-outline-gray-1">
              <button
                v-for="task in group.tasks"
                :key="task.name"
                class="flex w-full items-start gap-2 rounded px-1 py-2 text-left hover:bg-surface-gray-2"
                @click="$router.push(taskRoute(task))"
              >
                <TaskStatusIcon
                  :status="task.status"
                  :overdue="isTaskOverdue(task)"
                  class="mt-0.5 shrink-0"
                />
                <div class="min-w-0 flex-1">
                  <div class="line-clamp-2 text-sm font-semibold leading-5 text-ink-gray-8">{{ task.title }}</div>
                  <div class="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-gray-5">
                    <span>#{{ task.name }}</span>
                    <span v-if="task.priority">{{ task.priority }}</span>
                    <span v-if="task.due_date" :class="isTaskOverdue(task) ? 'text-red-500' : ''">
                      {{ $dayjs(task.due_date).format('D MMM') }}
                    </span>
                  </div>
                </div>
              </button>
            </div>
          </details>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import UserAvatar from './UserAvatar.vue'
import { getUser } from '@/data/users'

const STATUS_ORDER = ['In Progress', 'Under Testing', 'Ready to Merge', 'Todo', 'Backlog', 'Done', 'Cancelled', 'Reopen']
const STATUS_META = {
  Backlog: { dotClass: 'bg-gray-400', barClass: 'bg-gray-400' },
  Todo: { dotClass: 'bg-amber-500', barClass: 'bg-amber-500' },
  'In Progress': { dotClass: 'bg-pink-500', barClass: 'bg-pink-500' },
  'Under Testing': { dotClass: 'bg-purple-500', barClass: 'bg-purple-500' },
  'Ready to Merge': { dotClass: 'bg-indigo-500', barClass: 'bg-indigo-500' },
  Done: { dotClass: 'bg-green-500', barClass: 'bg-green-500' },
  Cancelled: { dotClass: 'bg-red-500', barClass: 'bg-red-500' },
  Reopen: { dotClass: 'bg-orange-500', barClass: 'bg-orange-500' },
}

export default {
  name: 'TeamView',
  components: {
    TaskStatusIcon,
    UserAvatar,
  },
  props: {
    tasks: { type: Array, required: true },
    assigneeIds: { type: Function, required: true },
    taskRoute: { type: Function, required: true },
    isTaskOverdue: { type: Function, required: true },
  },
  emits: ['request-new-task'],
  methods: {
    statusMeta(status) {
      return STATUS_META[status] || { dotClass: 'bg-gray-300', barClass: 'bg-gray-300' }
    },
    onAddTask(member) {
      const payload = {}
      if (member.id && member.id !== 'unassigned') {
        payload.assigned_to = member.id
      }
      this.$emit('request-new-task', payload)
    },
  },
  computed: {
    memberProgress() {
      const membersById = new Map()
      const ensureMember = (id) => {
        if (!membersById.has(id)) {
          const user = id === 'unassigned' ? null : getUser(id)
          membersById.set(id, {
            id,
            user,
            label: user?.full_name || 'Unassigned',
            tasks: [],
          })
        }
        return membersById.get(id)
      }

      for (const task of this.tasks) {
        const assignees = this.assigneeIds(task)
        if (!assignees.length) {
          ensureMember('unassigned').tasks.push(task)
          continue
        }
        for (const assignee of assignees) {
          ensureMember(assignee).tasks.push(task)
        }
      }

      return Array.from(membersById.values())
        .map((member) => {
          const done = member.tasks.filter((task) => task.status === 'Done').length
          const total = member.tasks.length
          const groups = new Map()
          for (const task of member.tasks) {
            const status = task.status || 'No Status'
            if (!groups.has(status)) groups.set(status, [])
            groups.get(status).push(task)
          }
          return {
            ...member,
            total,
            done,
            notDone: total - done,
            donePercent: total ? Math.round((done / total) * 100) : 0,
            statusGroups: Array.from(groups.entries())
              .sort(([a], [b]) => {
                const aIndex = STATUS_ORDER.indexOf(a)
                const bIndex = STATUS_ORDER.indexOf(b)
                return (aIndex === -1 ? 999 : aIndex) - (bIndex === -1 ? 999 : bIndex)
              })
              .map(([status, tasks]) => ({ status, tasks })),
          }
        })
        .sort((a, b) => {
          if (a.id === 'unassigned') return -1
          if (b.id === 'unassigned') return 1
          return a.label.localeCompare(b.label)
        })
    },
  },
}
</script>

<style scoped>
.team-card-scroll {
  scrollbar-width: thin;
}
</style>
