<template>
  <div class="flex h-full flex-1" v-if="$resources.task.doc">
    <div class="w-full flex-1">
      <div class="relative p-6">
        <div class="absolute right-0 top-0 p-6" v-show="$resources.task.setValueDebounced.loading">
          <LoadingText v-if="!$resources.task.setValueDebounced.error" text="Saving..." />
          <ErrorMessage :message="$resources.task.setValueDebounced.error" />
        </div>
        <div class="mb-2 flex items-center justify-between space-x-2">
          <input
            type="text"
            placeholder="Title"
            class="-ml-0.5 w-full rounded-sm border-none p-0.5 text-2xl bg-surface-white font-semibold text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
            @change="
              $resources.task.setValueDebounced.submit({
                title: $event.target.value,
              })
            "
            v-model="$resources.task.doc.title"
            v-focus
          />
          <Dropdown
            :options="[
              {
                label: 'Delete',
                onClick: () => {
                  $dialog({
                    title: 'Delete task',
                    message: 'Are you sure you want to delete this task?',
                    actions: [
                      {
                        label: 'Delete',
                        theme: 'red',
                        variant: 'solid',
                        onClick(close) {
                          return $resources.task.delete.submit(null, {
                            onSuccess() {
                              close()
                              $router.back()
                            },
                          })
                        },
                      },
                    ],
                  })
                },
              },
            ]"
          >
            <Button variant="ghost">
              <template #icon><LucideMoreHorizontal class="h-4 w-4" /></template>
            </Button>
          </Dropdown>
        </div>
        <TextEditor
          ref="description"
          editor-class="prose-sm max-w-none focus-within:ring-2 focus-within:ring-outline-gray-3 rounded-sm p-0.5 -ml-0.5 min-h-[4rem]"
          placeholder="Description"
          :content="$resources.task.doc.description"
          :bubbleMenu="true"
          :floatingMenu="true"
          @blur="
            !$refs.description.editor.isEmpty
              ? $resources.task.setValueDebounced.submit({
                  description: $refs.description.editor.getHTML(),
                })
              : null
          "
        />
        <div class="mt-8 flex flex-wrap items-center gap-2 sm:hidden">
          <div class="flex min-w-0 flex-col gap-2">
            <div class="flex flex-wrap gap-1">
              <span
                v-for="uid in assigneeUserIds"
                :key="uid"
                class="inline-flex items-center gap-1 rounded bg-surface-gray-2 px-2 py-0.5 text-sm text-ink-gray-8"
              >
                {{ $user(uid).full_name }}
                <button
                  type="button"
                  class="leading-none text-ink-gray-5 hover:text-ink-gray-8"
                  aria-label="Remove assignee"
                  @click="removeAssignee(uid)"
                >
                  ×
                </button>
              </span>
            </div>
            <Autocomplete
              placeholder="Add assignee"
              :options="assignableUsersForPicker"
              v-model="assigneeAddSelection"
              @update:modelValue="onAssigneePicked"
            />
          </div>
          <DatePicker
            v-model="$resources.task.doc.due_date"
            variant="subtle"
            placeholder="Due date"
            :disabled="false"
            @update:modelValue="
              $resources.task.setValue.submit({
                due_date: $event,
              })
            "
          />
          <Dropdown :options="statusOptions">
            <Button>
              <template #prefix>
                <TaskStatusIcon :status="$resources.task.doc.status" />
              </template>
              {{ $resources.task.doc.status || 'Set status' }}
            </Button>
          </Dropdown>
          <Dropdown :options="priorityOptions">
            <Button>
              <template v-if="$resources.task.doc.priority" #prefix>
                <TaskPriorityIcon :priority="$resources.task.doc.priority" />
              </template>
              {{ $resources.task.doc.priority || 'Set priority' }}
            </Button>
          </Dropdown>
          <Autocomplete
            placeholder="Select project"
            :options="projectOptions"
            v-model="selectedProject"
            @update:modelValue="changeProject"
          />
        </div>
        <CommentsList class="mt-8" doctype="GP Task" :name="taskId" />
      </div>
    </div>
    <div class="hidden w-[20rem] shrink-0 border-l sm:block">
      <div class="grid grid-cols-2 items-center gap-y-6 p-6 text-base text-ink-gray-7">
        <div>Assignees</div>
        <div class="space-y-2">
          <div class="flex flex-wrap gap-1">
            <span
              v-for="uid in assigneeUserIds"
              :key="uid"
              class="inline-flex items-center gap-1 rounded bg-surface-gray-2 px-2 py-0.5 text-sm text-ink-gray-8"
            >
              {{ $user(uid).full_name }}
              <button
                type="button"
                class="leading-none text-ink-gray-5 hover:text-ink-gray-8"
                aria-label="Remove assignee"
                @click="removeAssignee(uid)"
              >
                ×
              </button>
            </span>
          </div>
          <Autocomplete
            placeholder="Add assignee"
            :options="assignableUsersForPicker"
            v-model="assigneeAddSelection"
            @update:modelValue="onAssigneePicked"
          />
        </div>
        <div>Due Date</div>
        <div>
          <DatePicker
            v-model="$resources.task.doc.due_date"
            variant="subtle"
            placeholder="Due date"
            :disabled="false"
            @update:modelValue="
              $resources.task.setValue.submit({
                due_date: $event,
              })
            "
          />
        </div>
        <div>Project</div>
        <div>
          <Autocomplete
            placeholder="Select project"
            :options="projectOptions"
            v-model="selectedProject"
            @update:modelValue="changeProject"
          />
        </div>
        <div>Linked Teams</div>
        <div class="space-y-2">
          <div v-if="linkedTeams.length" class="space-y-1">
            <div
              v-for="team in linkedTeams"
              :key="team.name"
              class="flex items-center justify-between gap-2 rounded bg-surface-gray-2 px-2 py-1"
            >
              <span class="truncate text-base text-ink-gray-8">{{
                team.team_title || team.team
              }}</span>
              <Button
                variant="ghost"
                @click="unlinkTeam(team.team)"
                :loading="$resources.task.unlinkTeam.loading"
              >
                Remove
              </Button>
            </div>
          </div>
          <Autocomplete
            placeholder="Link a team"
            :options="linkableTeamOptions"
            v-model="linkedTeam"
            @update:modelValue="linkTeam"
          />
        </div>
        <div>Status</div>
        <div>
          <Dropdown :options="statusOptions">
            <Button>
              <template #prefix>
                <TaskStatusIcon :status="$resources.task.doc.status" />
              </template>
              {{ $resources.task.doc.status || 'Set status' }}
            </Button>
          </Dropdown>
        </div>
        <div>Priority</div>
        <div>
          <Dropdown :options="priorityOptions">
            <Button>
              <template v-if="$resources.task.doc.priority" #prefix>
                <TaskPriorityIcon :priority="$resources.task.doc.priority" />
              </template>
              {{ $resources.task.doc.priority || 'Set priority' }}
            </Button>
          </Dropdown>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { h } from 'vue'
import TextEditor from '@/components/TextEditor.vue'
import ReadmeEditor from '@/components/ReadmeEditor.vue'
import CommentsArea from '@/components/CommentsArea.vue'
import { focus } from '@/directives'
import { Autocomplete, Dropdown, LoadingText, DatePicker } from 'frappe-ui'
import CommentsList from '@/components/CommentsList.vue'
import TaskStatusIcon from '@/components/icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/icons/TaskPriorityIcon.vue'
import { activeUsers } from '@/data/users'
import { activeTeams } from '@/data/teams'
import { getTeamProjects } from '@/data/projects'

export default {
  name: 'TaskDetail',
  props: ['taskId'],
  directives: { focus },
  resources: {
    task() {
      return {
        type: 'document',
        doctype: 'GP Task',
        name: this.taskId,
        whitelistedMethods: {
          trackVisit: 'track_visit',
          getLinkedTeams: 'get_linked_teams',
          linkTeam: 'link_team',
          unlinkTeam: 'unlink_team',
        },
        setValue: {
          onError(e) {
            let message = e.messages ? e.messages.join('\n') : e.message
            this.$toast({
              title: 'Task Update Error',
              text: message,
              icon: 'alert-circle',
              iconClasses: 'text-ink-red-4',
            })
          },
        },
        onSuccess(doc) {
          if (
            ['ProjectTaskDetail', 'Task'].includes(this.$route.name) &&
            Number(this.$route.params.taskId) === doc.name
          ) {
            this.$resources.task.trackVisit.submit()
          }
          this.$resources.task.getLinkedTeams.submit()
        },
      }
    },
  },
  data() {
    return {
      linkedTeam: null,
      assigneeAddSelection: null,
    }
  },
  methods: {
    onAssigneePicked(option) {
      this.assigneeAddSelection = null
      if (!option?.value) return
      if (this.assigneeUserIds.includes(option.value)) return
      this.persistAssignees([...this.assigneeUserIds, option.value])
    },
    persistAssignees(userIds) {
      this.$resources.task.setValue.submit({
        assignees: userIds.map((user) => ({ user })),
      })
    },
    removeAssignee(uid) {
      this.persistAssignees(this.assigneeUserIds.filter((u) => u !== uid))
    },
    changeProject(option) {
      this.$resources.task.setValue.submit(
        {
          project: option?.value || '',
        },
        {
          onSuccess() {
            this.updateRoute()
          },
        },
      )
    },
    linkTeam(option) {
      if (!option?.value) return
      this.$resources.task.linkTeam.submit(
        {
          team: option.value,
          source_project: this.$resources.task.doc.project || null,
        },
        {
          onSuccess: () => {
            this.linkedTeam = null
            this.$resources.task.getLinkedTeams.submit()
          },
        },
      )
    },
    unlinkTeam(team) {
      this.$resources.task.unlinkTeam.submit(
        { team },
        {
          onSuccess: () => {
            this.$resources.task.getLinkedTeams.submit()
          },
        },
      )
    },
    updateRoute() {
      let task = this.$resources.task.doc
      if (task) {
        this.$router.replace({
          name: task.project ? 'ProjectTaskDetail' : 'Task',
          params: {
            taskId: task.name,
            teamId: task.team,
            projectId: task.project,
          },
        })
      }
    },
  },
  computed: {
    assigneeUserIds() {
      const doc = this.$resources.task.doc
      if (!doc) return []
      const fromRows = (doc.assignees || []).map((r) => r.user).filter(Boolean)
      if (fromRows.length) return fromRows
      return doc.assigned_to ? [doc.assigned_to] : []
    },
    assignableUsers() {
      return activeUsers.value.map((user) => ({
        label: user.full_name,
        value: user.name,
      }))
    },
    assignableUsersForPicker() {
      const ids = new Set(this.assigneeUserIds)
      return this.assignableUsers.filter((o) => !ids.has(o.value))
    },
    statusOptions() {
      return ['Backlog', 'Todo', 'In Progress', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled'].map((status) => {
        return {
          icon: () => h(TaskStatusIcon, { status }),
          label: status,
          onClick: () => this.$resources.task.setValue.submit({ status }),
        }
      })
    },
    priorityOptions() {
      return ['Low', 'Medium', 'High'].map((priority) => {
        return {
          icon: () => h(TaskPriorityIcon, { priority }),
          label: priority,
          onClick: () => this.$resources.task.setValue.submit({ priority }),
        }
      })
    },
    projectOptions() {
      return activeTeams.value.map((team) => ({
        group: team.title,
        items: getTeamProjects(team.name).map((project) => ({
          label: project.title,
          value: project.name.toString(),
        })),
      }))
    },
    selectedProject: {
      get() {
        const projectId = this.$resources.task.doc?.project
        if (!projectId) return null
        for (const group of this.projectOptions) {
          const found = group.items.find((item) => item.value == projectId)
          if (found) return found
        }
        return null
      },
      set(option) {
        this.$resources.task.doc.project = option?.value || ''
      },
    },
    linkedTeams() {
      return this.$resources.task.getLinkedTeams.data || []
    },
    linkableTeamOptions() {
      const currentTeam = this.$resources.task.doc?.team
      const linkedTeams = this.linkedTeams.map((team) => team.team)
      return activeTeams.value
        .filter((team) => team.name !== currentTeam && !linkedTeams.includes(team.name))
        .map((team) => ({
          label: team.title,
          value: team.name,
        }))
    },
  },
  components: {
    ReadmeEditor,
    TextEditor,
    CommentsArea,
    Autocomplete,
    Dropdown,
    CommentsList,
    TaskStatusIcon,
    LoadingText,
    TaskPriorityIcon,
    DatePicker,
  },
}
</script>
