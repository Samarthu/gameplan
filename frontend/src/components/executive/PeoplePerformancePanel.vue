<template>
  <div class="overflow-x-auto rounded-lg border bg-surface-white">
    <table class="min-w-full divide-y divide-outline-gray-2 text-sm">
      <thead class="bg-surface-gray-1">
        <tr>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Person</th>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Performance</th>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Insight</th>
          <th class="px-4 py-3 text-left text-xs font-medium uppercase text-ink-gray-6">Teams</th>
          <th class="px-4 py-3 text-right text-xs font-medium uppercase text-ink-gray-6">Overdue</th>
          <th class="px-4 py-3 text-right text-xs font-medium uppercase text-ink-gray-6">Stale</th>
          <th class="px-4 py-3 text-right text-xs font-medium uppercase text-ink-gray-6">Done (wk)</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-outline-gray-2">
        <tr v-for="person in people" :key="person.user" class="hover:bg-surface-gray-1">
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <UserAvatar :user="person.user" />
              <span class="font-medium text-ink-gray-9">{{ person.full_name }}</span>
            </div>
          </td>
          <td class="px-4 py-3">
            <span
              class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold capitalize"
              :class="statusClass(person.status)"
            >
              {{ person.status === 'underperforming' ? 'Not performing' : 'Struggling' }}
            </span>
          </td>
          <td class="max-w-xs px-4 py-3 text-ink-gray-7">{{ person.insight }}</td>
          <td class="px-4 py-3 text-xs text-ink-gray-6">{{ person.teams || '—' }}</td>
          <td class="px-4 py-3 text-right font-semibold text-red-700">{{ person.overdue_count }}</td>
          <td class="px-4 py-3 text-right text-ink-gray-8">{{ person.stale_count }}</td>
          <td class="px-4 py-3 text-right text-ink-gray-8">{{ person.completed_7d }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!people.length" class="px-4 py-8 text-center text-sm text-ink-gray-5">
      No individuals with overdue workload flagged this week.
    </p>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'

defineProps({
  people: { type: Array, default: () => [] },
})

function statusClass(status) {
  if (status === 'underperforming') return 'bg-red-100 text-red-800'
  return 'bg-amber-100 text-amber-900'
}
</script>
