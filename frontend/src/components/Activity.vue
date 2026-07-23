<template>
  <div class="relative py-1 pl-10 pr-1 text-sm group/activity">
    <span
      class="absolute left-[17px] top-3 h-2.5 w-2.5 rounded-full border-2 border-surface-white bg-ink-gray-4 ring-1 ring-outline-gray-3"
      aria-hidden="true"
    ></span>
    <UserInfo :email="activity.user" v-slot="{ user }">
      <div class="flex min-w-0 items-start gap-2">
        <UserProfileLink :user="user.name" class="shrink-0">
          <UserAvatar :user="user.name" size="sm" />
        </UserProfileLink>
        <div class="min-w-0 flex-1">
          <div class="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-0.5 pr-10">
            <UserProfileLink
              class="text-base font-semibold leading-5 text-ink-gray-9 hover:text-ink-blue-3"
              :user="user.name"
            >
              {{ user.full_name }}
            </UserProfileLink>
            <time
              class="shrink-0 whitespace-nowrap text-sm text-ink-gray-5"
              :datetime="activity.creation"
              :title="$dayjs(activity.creation)"
            >
              {{ $dayjs(activity.creation).format('DD/MM/YYYY hh:mm A') }}
            </time>
          </div>
          <div class="mt-2 flex min-w-0 items-start gap-2">
            <span class="mt-2 h-px w-4 shrink-0 bg-outline-gray-2" aria-hidden="true"></span>
            <p class="min-w-0 text-sm leading-5 text-ink-gray-7">
              <span v-if="activity.action == 'Discussion Closed'">
                <span class="font-medium text-ink-gray-9">Closed</span> this discussion
              </span>
              <span v-else-if="activity.action == 'Discussion Reopened'">
                <span class="font-medium text-ink-gray-9">Reopened</span> this discussion
              </span>
              <span v-else-if="activity.action == 'Discussion Pinned'">
                <span class="font-medium text-ink-gray-9">Pinned</span> this discussion
              </span>
              <span v-else-if="activity.action == 'Discussion Unpinned'">
                <span class="font-medium text-ink-gray-9">Unpinned</span> this discussion
              </span>
              <span v-else-if="activity.action == 'Discussion Title Changed'">
                <span class="font-medium text-ink-gray-9">Title</span> changed from
                <span class="text-ink-gray-8">“{{ activity.data.old_title }}”</span> to
                <span class="text-ink-gray-8">“{{ activity.data.new_title }}”</span>
              </span>
              <span v-else-if="activity.action == 'Status On Hold'">
                Put on <span class="font-medium text-ink-gray-9">Hold</span> —
                <span class="text-ink-gray-8">“{{ activity.data.reason }}”</span>
              </span>
              <span v-else-if="activity.action == 'Timer Paused'">
                <span class="font-medium text-ink-gray-9">Paused</span> the timer at
                <span class="text-ink-gray-8">{{ formatDuration(activity.data.total_seconds) }}</span>
                — <span class="text-ink-gray-8">“{{ activity.data.reason }}”</span>
              </span>
              <span v-else-if="activity.action == 'Timer Stopped'">
                <span class="font-medium text-ink-gray-9">Stopped</span> the timer
                <template v-if="activity.data.status">
                  in <span class="text-ink-gray-8">{{ activity.data.status }}</span>
                </template>
                — total time
                <span class="text-ink-gray-8">{{ formatDuration(activity.data.total_seconds) }}</span>
              </span>
              <span v-else-if="activity.action == 'Task Value Changed'">
                <template v-if="activity.data.field === 'assigned_to'">
                  <span class="font-medium text-ink-gray-9">Assignee</span> set to
                  <UserProfileLink
                    class="font-medium text-ink-gray-8 hover:text-ink-gray-5"
                    :user="$user(activity.data.new_value).name"
                  >
                    {{ $user(activity.data.new_value).full_name }}
                  </UserProfileLink>
                </template>
                <template v-else-if="activity.data.field === 'assignees'">
                  <span class="font-medium text-ink-gray-9">Assignees</span> changed
                  <template v-if="assigneeIdList(activity.data.old_value).length">
                    from
                    <template v-for="(uid, i) in assigneeIdList(activity.data.old_value)" :key="uid">
                      <template v-if="i > 0">,&nbsp;</template>
                      <UserProfileLink
                        class="font-medium text-ink-gray-8 hover:text-ink-gray-5"
                        :user="$user(uid).name"
                      >
                        {{ $user(uid).full_name }}
                      </UserProfileLink>
                    </template>
                  </template>
                  &nbsp;to
                  <template v-for="(uid, i) in assigneeIdList(activity.data.new_value)" :key="'n' + uid">
                    <template v-if="i > 0">,&nbsp;</template>
                    <UserProfileLink
                      class="font-medium text-ink-gray-8 hover:text-ink-gray-5"
                      :user="$user(uid).name"
                    >
                      {{ $user(uid).full_name }}
                    </UserProfileLink>
                  </template>
                </template>
                <template v-else-if="activity.data.field === 'description'">
                  <span class="font-medium text-ink-gray-9">Description</span> updated
                </template>
                <template v-else-if="activity.data.field === 'project'">
                  <span class="font-medium text-ink-gray-9">Project</span>
                  <template v-if="activity.data.old_value">
                    changed from
                    <span class="text-ink-gray-8">{{ projectTitle(activity.data.old_value) }}</span> to
                  </template>
                  <template v-else> set to </template>
                  <span class="text-ink-gray-8">{{ projectTitle(activity.data.new_value) }}</span>
                </template>
                <template v-else>
                  <span class="font-medium text-ink-gray-9">{{ activity.data.field_label }}</span>
                  changed
                  <template v-if="activity.data.old_value">
                    from
                    <span class="text-ink-gray-8">{{ activity.data.old_value }}</span>
                    to
                  </template>
                  <template v-else> to </template>
                  <span class="text-ink-gray-8">{{ activity.data.new_value }}</span>
                </template>
              </span>
            </p>
          </div>
        </div>
        <button
          type="button"
          class="absolute right-1 top-1.5 rounded p-1 text-ink-gray-4 opacity-0 transition group-hover/activity:opacity-100 hover:bg-surface-gray-2 hover:text-ink-gray-7"
          :class="activity.pinned ? '!text-ink-blue-3 opacity-100' : ''"
          :title="activity.pinned ? 'Unpin' : 'Pin to top'"
          @click="$emit('toggle-pin')"
        >
          <LucidePin class="h-3.5 w-3.5" :class="activity.pinned ? 'fill-current' : ''" />
        </button>
        <span v-if="number && !activity.pinned" class="absolute right-8 top-2 text-sm text-ink-gray-5">#{{ number }}</span>
      </div>
    </UserInfo>
  </div>
</template>
<script>
import UserProfileLink from './UserProfileLink.vue'
import UserAvatar from './UserAvatar.vue'
import { projectTitle } from '@/utils/formatters'

export default {
  name: 'Activity',
  emits: ['toggle-pin'],
  props: {
    activity: {
      type: Object,
      required: true,
    },
    number: {
      type: Number,
      default: null,
    },
  },
  components: { UserProfileLink, UserAvatar },
  methods: {
    projectTitle,
    formatDuration(totalSeconds) {
      const s = Math.max(0, Math.floor(totalSeconds || 0))
      const hh = String(Math.floor(s / 3600)).padStart(2, '0')
      const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0')
      const ss = String(s % 60).padStart(2, '0')
      return `${hh}:${mm}:${ss}`
    },
    assigneeIdList(val) {
      if (val == null || val === '') return []
      if (Array.isArray(val)) return val.filter(Boolean)
      if (typeof val === 'string') {
        try {
          const p = JSON.parse(val)
          return Array.isArray(p) ? p.filter(Boolean) : []
        } catch {
          return []
        }
      }
      return []
    },
  },
}
</script>
