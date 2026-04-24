<template>
  <div class="sm:rounded sm:border sm:px-4 sm:py-3">
    <div class="mb-3 flex items-center justify-between">
      <h2 class="text-xl font-semibold text-ink-gray-8">Goals</h2>
      <div class="flex space-x-2" v-if="editable">
        <Tooltip v-if="!editing && !$readOnlyMode" text="Edit">
          <Button variant="ghost" label="Edit" @click="startEditing">
            <template #icon><LucideEdit2 class="w-4" /></template>
          </Button>
        </Tooltip>
        <template v-if="editing">
          <Button @click="save" :loading="project.setValue.loading">
            <template #prefix><LucideSave class="w-4" /></template>
            Save
          </Button>
          <Button @click="discard">
            <template #prefix><LucideRotateCcw class="w-4" /></template>
            Discard
          </Button>
        </template>
      </div>
    </div>

    <div v-if="!editing">
      <div v-if="goals.length === 0" class="text-base text-ink-gray-5">
        No goals yet — click Edit to add up to {{ goalLimit }} goals.
      </div>
      <ul v-else class="space-y-2">
        <li
          v-for="(goal, i) in goals"
          :key="goal.name || i"
          class="flex items-center gap-3"
        >
          <span
            class="inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-xs font-medium"
            :class="statusPillClass(goal.status)"
          >
            {{ goal.status || 'On Track' }}
          </span>
          <span
            class="text-base text-ink-gray-8"
            :class="{ 'text-ink-gray-5 line-through': goal.status === 'Done' }"
          >
            {{ goal.title }}
          </span>
        </li>
      </ul>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="(goal, i) in local"
        :key="i"
        class="flex items-center gap-2"
      >
        <FormControl
          class="flex-1"
          v-model="goal.title"
          placeholder="Goal title"
          autocomplete="off"
        />
        <FormControl
          type="select"
          :options="statusOptions"
          v-model="goal.status"
        />
        <Tooltip text="Remove">
          <Button variant="ghost" @click="removeRow(i)">
            <template #icon><LucideTrash2 class="w-4" /></template>
          </Button>
        </Tooltip>
      </div>
      <Button
        variant="ghost"
        @click="addRow"
        :disabled="local.length >= goalLimit"
        :title="local.length >= goalLimit ? `Maximum ${goalLimit} goals` : ''"
      >
        <template #prefix><LucidePlus class="w-4" /></template>
        Add goal
      </Button>
      <ErrorMessage class="mt-2" :message="project.setValue.error" />
    </div>
  </div>
</template>

<script>
import { Button, FormControl, Tooltip, ErrorMessage } from 'frappe-ui'

export default {
  name: 'ProjectOverviewGoals',
  props: ['project'],
  components: {
    Button,
    FormControl,
    Tooltip,
    ErrorMessage,
  },
  data() {
    return {
      editing: false,
      local: [],
      statusOptions: ['On Track', 'At Risk', 'Done'],
    }
  },
  computed: {
    goals() {
      return this.project.doc.goals || []
    },
    goalLimit() {
      const max = Number(this.project.doc.max_goal_limit || 3)
      const safeMax = Number.isFinite(max) && max > 0 ? Math.floor(max) : 3
      const n = Number(this.project.doc.goal_limit || safeMax)
      if (!Number.isFinite(n)) return safeMax
      if (n < 1) return 1
      if (n > safeMax) return safeMax
      return n
    },
    editable() {
      return !this.project.doc.archived_at
    },
  },
  methods: {
    statusPillClass(status) {
      if (status === 'At Risk') return 'bg-yellow-100 text-yellow-700'
      if (status === 'Done') return 'bg-gray-100 text-gray-600'
      return 'bg-green-100 text-green-700'
    },
    startEditing() {
      this.local = this.goals.map((g) => ({
        title: g.title || '',
        status: g.status || 'On Track',
      }))
      this.editing = true
    },
    addRow() {
      if (this.local.length >= this.goalLimit) return
      this.local.push({ title: '', status: 'On Track' })
    },
    removeRow(i) {
      this.local.splice(i, 1)
    },
    async save() {
      const payload = this.local
        .filter((g) => (g.title || '').trim())
        .map((g) => ({ title: g.title.trim(), status: g.status || 'On Track' }))
      if (payload.length > this.goalLimit) {
        return
      }
      try {
        await this.project.setValue.submit({ goals: payload })
        this.editing = false
      } catch (e) {
        // ErrorMessage component shows project.setValue.error
      }
    },
    discard() {
      this.editing = false
      this.local = []
      this.project.reload()
    },
  },
}
</script>
