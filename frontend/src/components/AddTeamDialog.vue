<template>
  <Dialog :options="{ title: 'Add Team' }" v-model="showDialog">
    <template #body-main>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-6 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">Add Team</h3>
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
            label="Team Name"
            type="text"
            v-model="newTeam.title"
            placeholder="Team Name"
            @keydown.enter="createTeam($event.target.value)"
            autocomplete="off"
          />
          <FormControl
            type="select"
            label="Visibility"
            :options="[
              { label: 'Visible to everyone', value: 0 },
              { label: 'Visible to team members (Private)', value: 1 },
            ]"
            v-model="newTeam.is_private"
          />
          <ErrorMessage :message="teams.insert.error?.messages" />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        class="w-full"
        @click="createTeam(teamName)"
        :loading="teams.insert.loading"
      >
        Create Team
      </Button>
    </template>
  </Dialog>
  <div
    v-if="minimized"
    class="fixed bottom-4 right-4 z-20 flex w-72 items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3 shadow-xl"
  >
    <button
      class="min-w-0 flex-1 truncate text-left text-sm font-medium text-ink-gray-8"
      @click="expand"
    >
      {{ newTeam.title || 'Add Team' }}
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
import { teams } from '@/data/teams'

export default {
  name: 'AddTeamDialog',
  props: ['show'],
  emits: ['success', 'update:show'],
  data() {
    return {
      newTeam: { title: '', is_private: 0 },
      minimized: false,
      teams,
    }
  },
  methods: {
    createTeam() {
      teams.insert.submit(this.newTeam, {
        onSuccess: (team) => {
          this.$resetData('newTeam')
          this.minimized = false
          this.showDialog = false
          this.$emit('success', team)
        },
      })
    },
    minimize() {
      this.minimized = true
      this.showDialog = false
    },
    expand() {
      this.minimized = false
      this.showDialog = true
    },
    closeDialog() {
      this.minimized = false
      this.showDialog = false
    },
    closeFromPill() {
      this.minimized = false
      this.$resetData('newTeam')
    },
  },
  computed: {
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
