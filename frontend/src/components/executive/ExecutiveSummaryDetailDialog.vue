<template>
  <Dialog :options="{ title, size: '4xl' }" v-model="open">
    <template #body-main>
      <div class="max-h-[70vh] overflow-y-auto bg-surface-modal px-4 py-4 sm:px-6">
        <p v-if="description" class="mb-4 text-sm text-ink-gray-6">{{ description }}</p>

        <!-- Teams in red -->
        <ul v-if="drilldown === 'teams_red'" class="divide-y divide-outline-gray-2">
          <li
            v-for="team in items"
            :key="team.name"
            class="flex flex-wrap items-center justify-between gap-3 py-3"
          >
            <div class="min-w-0">
              <router-link
                :to="{ name: 'TeamOverview', params: { teamId: team.name } }"
                class="font-medium text-ink-gray-9 hover:underline"
                @click="open = false"
              >
                {{ team.icon }} {{ team.title }}
              </router-link>
              <p class="mt-1 text-xs text-ink-gray-6">{{ team.insight }}</p>
            </div>
            <div class="flex items-center gap-3 text-sm">
              <span>{{ team.lead_name || 'No lead' }}</span>
              <span class="font-medium text-red-700">{{ team.metrics?.overdue_count }} overdue</span>
              <HealthBadge :health="team.health" />
            </div>
          </li>
        </ul>

        <!-- Leads at risk / no team lead -->
        <ul
          v-else-if="drilldown === 'leads_at_risk' || drilldown === 'no_team_lead'"
          class="divide-y divide-outline-gray-2"
        >
          <li
            v-for="row in items"
            :key="row.team || row.name"
            class="flex flex-wrap items-center justify-between gap-3 py-3"
          >
            <div class="min-w-0">
              <router-link
                :to="{ name: 'TeamOverview', params: { teamId: row.team || row.name } }"
                class="font-medium text-ink-gray-9 hover:underline"
                @click="open = false"
              >
                {{ row.team_icon || row.icon }} {{ row.team_title || row.title }}
              </router-link>
              <p class="mt-1 text-xs text-ink-gray-6">{{ row.insight }}</p>
            </div>
            <div class="flex items-center gap-2">
              <UserAvatar v-if="row.lead" :user="row.lead" />
              <span :class="row.lead ? 'text-ink-gray-8' : 'font-medium text-red-700'">
                {{ row.lead_name || 'Not assigned' }}
              </span>
            </div>
          </li>
        </ul>

        <!-- People behind -->
        <ul v-else-if="drilldown === 'people_behind'" class="divide-y divide-outline-gray-2">
          <li
            v-for="person in items"
            :key="person.user"
            class="flex flex-wrap items-center justify-between gap-3 py-3"
          >
            <div class="flex items-center gap-2">
              <UserAvatar :user="person.user" />
              <div>
                <p class="font-medium text-ink-gray-9">{{ person.full_name }}</p>
                <p class="text-xs text-ink-gray-6">{{ person.insight }}</p>
              </div>
            </div>
            <div class="text-right text-sm">
              <p class="font-semibold text-red-700">{{ person.overdue_count }} overdue</p>
              <p class="text-ink-gray-6">{{ person.completed_7d }} done this week</p>
            </div>
          </li>
        </ul>

        <!-- Overdue tasks -->
        <div v-else-if="drilldown === 'overdue_tasks'">
          <h3 class="mb-2 text-sm font-semibold text-ink-gray-8">By team</h3>
          <ul class="mb-6 divide-y divide-outline-gray-2">
            <li
              v-for="team in teamBreakdown"
              :key="team.name"
              class="flex items-center justify-between py-2 text-sm"
            >
              <router-link
                :to="{ name: 'TeamTasks', params: { teamId: team.name } }"
                class="hover:underline"
                @click="open = false"
              >
                {{ team.icon }} {{ team.title }}
              </router-link>
              <span class="font-medium">{{ team.metrics?.overdue_count }} overdue</span>
            </li>
          </ul>
          <h3 v-if="taskItems.length" class="mb-2 text-sm font-semibold text-ink-gray-8">
            Top overdue tasks
          </h3>
          <ul class="divide-y divide-outline-gray-2">
            <li
              v-for="task in taskItems"
              :key="task.task"
              class="flex flex-wrap items-center justify-between gap-2 py-3 text-sm"
            >
              <div class="min-w-0">
                <router-link
                  v-if="task.task"
                  :to="{ name: 'Task', params: { taskId: task.task } }"
                  class="font-medium hover:underline"
                  @click="open = false"
                >
                  {{ task.title }}
                </router-link>
                <span v-else>{{ task.title }}</span>
                <p class="text-xs text-ink-gray-5">
                  {{ task.days_late }} days late
                  <span v-if="task.owner_user"> · {{ task.owner_user }}</span>
                </p>
              </div>
              <Button
                v-if="task.task"
                size="sm"
                variant="outline"
                :route="{ name: 'Task', params: { taskId: task.task } }"
                @click="open = false"
              >
                Open
              </Button>
            </li>
          </ul>
          <p v-if="unassignedOverdue" class="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900">
            {{ unassignedOverdue }} overdue task(s) have no assignee.
          </p>
        </div>

        <!-- Closed this week -->
        <ul v-else-if="drilldown === 'closed_week'" class="divide-y divide-outline-gray-2">
          <li
            v-for="team in items"
            :key="team.name"
            class="flex items-center justify-between py-3 text-sm"
          >
            <router-link
              :to="{ name: 'TeamOverview', params: { teamId: team.name } }"
              class="font-medium hover:underline"
              @click="open = false"
            >
              {{ team.icon }} {{ team.title }}
            </router-link>
            <span class="font-medium text-green-800">{{ team.metrics?.completed_7d }} completed</span>
          </li>
        </ul>

        <p v-if="!hasItems && drilldown !== 'overdue_tasks'" class="py-8 text-center text-sm text-ink-gray-5">
          Nothing to show for this metric.
        </p>
        <p
          v-if="drilldown === 'closed_week' && !hasItems"
          class="py-8 text-center text-sm text-ink-gray-5"
        >
          No tasks were marked completed this week org-wide.
        </p>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { computed } from 'vue'
import { Dialog, Button } from 'frappe-ui'
import HealthBadge from './HealthBadge.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const open = defineModel({ type: Boolean, default: false })

const props = defineProps({
  drilldown: { type: String, default: '' },
  title: { type: String, default: 'Details' },
  description: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  teams: { type: Array, default: () => [] },
  escalations: { type: Array, default: () => [] },
  unassignedOverdue: { type: Number, default: 0 },
})

const teamBreakdown = computed(() => {
  return [...props.teams]
    .filter((t) => (t.metrics?.overdue_count || 0) > 0)
    .sort((a, b) => (b.metrics?.overdue_count || 0) - (a.metrics?.overdue_count || 0))
})

const taskItems = computed(() =>
  props.escalations.filter((e) => e.type === 'overdue_task')
)

const hasItems = computed(() => {
  if (props.drilldown === 'overdue_tasks') {
    return teamBreakdown.value.length > 0 || taskItems.value.length > 0
  }
  return props.items.length > 0
})
</script>
