<template>
  <Dialog :options="{ title: 'Create Sprint' }" v-model="showDialog">
    <template #body-content>
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
</template>
<script>
import { sprints } from '@/data/sprints'

export default {
  name: 'AddSprintDialog',
  props: ['show', 'team'],
  emits: ['success', 'update:show'],
  data() {
    return {
      newSprint: { title: '', status: 'Planned', start_date: '', end_date: '' },
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
            this.showDialog = false
            this.$emit('success', sprint)
          },
        },
      )
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
