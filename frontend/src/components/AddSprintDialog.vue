<template>
  <Dialog :options="{ title: 'Create Sprint' }" v-model="showDialog">
    <template #body-main>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">Create Sprint</h3>
          <div class="flex items-center gap-1">
            <Button variant="ghost" @click="minimize">
              <template #icon>
                <LucideMinimize2 class="h-4 w-4 text-ink-gray-9" />
              </template>
            </Button>
            <Button variant="ghost" @click="closeDialog">
              <template #icon>
                <LucideX class="h-4 w-4 text-ink-gray-9" />
              </template>
            </Button>
          </div>
        </div>
        <div class="space-y-4">
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
    class="fixed z-20 flex w-72 items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3 shadow-xl"
  >
    <button
      class="min-w-0 flex-1 truncate text-left text-sm font-medium text-ink-gray-8"
      @click="expand"
    >
      {{ newSprint.title || 'Create Sprint' }}
    </button>
    <div class="flex shrink-0 items-center gap-1">
      <button
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Expand"
        @click="expand"
      >
        <LucideMaximize2 class="h-4 w-4" />
      </button>
      <button
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Close"
        @click="closeFromPill"
      >
        <LucideX class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
<script>
import { sprints } from '@/data/sprints'
import { nextStackId, pushStack, removeStack, pillStyle } from '@/utils/minimizedStack'

export default {
  name: 'AddSprintDialog',
  props: ['show', 'team'],
  emits: ['success', 'update:show'],
  data() {
    return {
      newSprint: { title: '', status: 'Planned', start_date: '', end_date: '' },
      minimized: false,
      stackId: nextStackId(),
      sprints,
    }
  },
  methods: {
    createSprint() {
      sprints.insert.submit(
        { ...this.newSprint, team: this.team },
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
