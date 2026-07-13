<template>
  <Dialog :options="{ title: 'Create Sprint' }" v-model="showDialog">
    <template #body-main>
      <div class="px-4 pt-5 pb-6 bg-surface-modal sm:px-6">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">Create Sprint</h3>
          <div class="flex items-center gap-1">
            <Button variant="ghost" @click="minimize">
              <template #icon>
                <LucideMinimize2 class="w-4 h-4 text-ink-gray-9" />
              </template>
            </Button>
            <Button variant="ghost" @click="closeDialog">
              <template #icon>
                <LucideX class="w-4 h-4 text-ink-gray-9" />
              </template>
            </Button>
          </div>
        </div>
        <div class="space-y-4">
          <div class="space-y-2">
            <div class="text-sm text-ink-gray-7">Team</div>
            <Autocomplete
              placeholder="Select team"
              :options="teamOptions"
              v-model="selectedTeam"
            />
          </div>
          <FormControl
          label="Sprint Name (optional)"
          type="text"
          v-model="newSprint.title"
          placeholder="Auto-generated from dates if left empty"
          autocomplete="off"
        />
        <FormControl
          type="select"
          label="Status"
          :options="[
            { label: 'Planned', value: 'Planned' },
            { label: 'Active', value: 'Active' },
            { label: 'Completed', value: 'Completed' },
          ]"
          v-model="newSprint.status"
        />
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            label="Start Date"
            type="date"
            v-model="newSprint.start_date"
          />
          <FormControl
            label="End Date"
            type="date"
            v-model="newSprint.end_date"
          />
        </div>
        <ErrorMessage :message="sprints.insert.error?.messages" />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="w-full"
        @click="createSprint"
        :loading="sprints.insert.loading"
      >
        Create Sprint
      </Button>
    </template>
  </Dialog>
  <div
    v-if="minimized"
    :style="pillStyle"
    class="fixed z-20 flex items-center justify-between gap-3 px-4 py-3 border rounded-lg shadow-xl w-72 border-outline-gray-2 bg-surface-white"
  >
    <button
      class="flex-1 min-w-0 text-sm font-medium text-left truncate text-ink-gray-8"
      @click="expand"
    >
      {{ newSprint.title || 'Create Sprint' }}
    </button>
    <div class="flex items-center gap-1 shrink-0">
      <button
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Expand"
        @click="expand"
      >
        <LucideMaximize2 class="w-4 h-4" />
      </button>
      <button
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Close"
        @click="closeFromPill"
      >
        <LucideX class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>
<script>
import { Autocomplete } from 'frappe-ui'
import { sprints } from '@/data/sprints'
import { activeTeams } from '@/data/teams'
import { nextStackId, pushStack, removeStack, pillStyle } from '@/utils/minimizedStack'

export default {
  name: 'AddSprintDialog',
  components: { Autocomplete },
  props: ['show', 'team', 'project'],
  emits: ['success', 'update:show'],
  data() {
    return {
      newSprint: { title: '', status: 'Planned', start_date: '', end_date: '' },
      teamValue: this.team,
      minimized: false,
      stackId: nextStackId(),
      sprints,
    }
  },
  watch: {
    team(val) {
      this.teamValue = val
    },
  },
  methods: {
    createSprint() {
      sprints.insert.submit(
        { ...this.newSprint, team: this.teamValue, project: this.project || null },
        {
          onSuccess: (sprint) => {
            this.$resetData('newSprint')
            this.minimized = false
            removeStack(this.stackId)
            this.showDialog = false
            this.$emit('success', sprint)
          },
        },
      )
    },
    minimize() {
      this.minimized = true
      pushStack(this.stackId)
      this.showDialog = false
    },
    expand() {
      this.minimized = false
      removeStack(this.stackId)
      this.showDialog = true
    },
    closeDialog() {
      this.minimized = false
      removeStack(this.stackId)
      this.showDialog = false
    },
    closeFromPill() {
      this.minimized = false
      removeStack(this.stackId)
      this.$resetData('newSprint')
    },
  },
  computed: {
    pillStyle() {
      return pillStyle(this.stackId).value
    },
    teamOptions() {
      return activeTeams.value.map((team) => ({
        label: team.title,
        value: team.name,
      }))
    },
    selectedTeam: {
      get() {
        if (!this.teamValue) return null
        return this.teamOptions.find((o) => o.value == this.teamValue) || null
      },
      set(option) {
        this.teamValue = option?.value || null
      },
    },
    showDialog: {
      get() {
        return this.show
      },
      set(val) {
        this.$emit('update:show', val)
      },
    },
  },
}
</script>
