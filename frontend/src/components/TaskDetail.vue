<template>
  <div class="flex flex-1 h-full" v-if="$resources.task.doc">
    <div class="min-w-[420px] flex-1 overflow-y-auto border-r border-outline-gray-2">
      <div class="relative p-6">
        <div class="absolute top-0 right-0 p-6" v-show="$resources.task.setValueDebounced.loading">
          <LoadingText v-if="!$resources.task.setValueDebounced.error" text="Saving..." />
          <ErrorMessage :message="$resources.task.setValueDebounced.error" />
        </div>
        <div class="flex items-center justify-between gap-2 mb-6">
          <Dropdown :options="taskTypeOptions">
            <Button class="whitespace-nowrap">
              <template #prefix>
                <LucideCircle class="w-4 h-4" />
              </template>
              {{ $resources.task.doc.task_type || 'Task' }}
            </Button>
          </Dropdown>
          <Dropdown
            v-if="canDeleteTask"
            :options="[
              {
                label: 'Delete',
                onClick: () => {
                  const unlink = Boolean($resources.task.doc.project && $resources.task.doc.sprint)
                  $dialog({
                    title: unlink ? 'Remove sprint link' : 'Delete task',
                    message: unlink
                      ? 'This task is linked to both a project and a sprint, so only the sprint link will be removed (not deleted).'
                      : 'Are you sure you want to delete this task?',
                    actions: [
                      {
                        label: unlink ? 'Remove link' : 'Delete',
                        theme: 'red',
                        variant: 'solid',
                        onClick(close) {
                          if (unlink) {
                            return $resources.task.setValue.submit(
                              { sprint: '' },
                              { onSuccess: () => close() },
                            )
                          }
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
              <template #icon><LucideMoreHorizontal class="w-4 h-4" /></template>
            </Button>
          </Dropdown>
        </div>
        <div class="mb-3">
          <textarea
            ref="titleTextarea"
            rows="1"
            placeholder="Title"
            class="-ml-0.5 w-full resize-none overflow-hidden rounded-sm border-none bg-surface-white p-0.5 text-2xl font-semibold text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
            @change="
              $resources.task.setValueDebounced.submit({
                title: $event.target.value,
              })
            "
            @keydown.enter.prevent="$event.target.blur()"
            @input="resizeTitle"
            v-model="$resources.task.doc.title"
            v-focus
            maxlength="140"
          ></textarea>
        </div>
        <div class="grid max-w-4xl grid-cols-1 pb-4 mb-4 text-sm border-b gap-x-6 gap-y-1.5 border-outline-gray-2 text-ink-gray-7 md:grid-cols-2">
          <div class="grid grid-cols-[6.5rem_minmax(0,1fr)] items-center gap-x-2 gap-y-1.5 content-start">
            <template v-if="$resources.task.doc.parent_task">
              <div class="text-ink-gray-6">Parent Task</div>
              <button
                class="flex min-w-0 items-center gap-1.5 rounded px-1.5 py-1 text-left text-sm text-ink-gray-8 hover:bg-surface-gray-2"
                @click="openParentTask"
              >
                <LucideCornerLeftUp class="h-3.5 w-3.5 shrink-0 text-ink-gray-4" />
                <span class="truncate">{{ parentTaskTitle || '#' + $resources.task.doc.parent_task }}</span>
              </button>
            </template>
            <div class="text-ink-gray-6">Status</div>
            <Dropdown :options="statusOptions">
              <Button class="whitespace-nowrap">
                <template #prefix>
                  <TaskStatusIcon :status="$resources.task.doc.status" />
                </template>
                {{ $resources.task.doc.status || 'Set status' }}
              </Button>
            </Dropdown>
            <div class="flex items-center gap-1 text-ink-gray-6">
              Due
              <button
                type="button"
                class="rounded p-0.5 text-ink-gray-4 hover:bg-surface-gray-2 hover:text-ink-gray-7"
                title="Due date revision history"
                @click="openDueHistory"
              >
                <LucideHistory class="h-3.5 w-3.5" />
              </button>
            </div>
            <DatePicker
              v-model="$resources.task.doc.due_date"
              variant="subtle"
              placeholder="Due date"
              :disabled="false"
              @update:modelValue="onDueDateChange"
            />
            <div class="text-ink-gray-6">Project</div>
            <Autocomplete
              placeholder="Select project"
              :options="projectOptions"
              v-model="selectedProject"
              @update:modelValue="changeProject"
            />
            <div class="text-ink-gray-6">Completed</div>
            <div
              v-if="isAutoCompletion"
              class="px-1.5 py-1 text-sm text-ink-gray-8"
              title="Set automatically for Done and Live"
            >
              {{ completedDate || '—' }}
            </div>
            <DatePicker
              v-else
              v-model="$resources.task.doc.completed_at"
              variant="subtle"
              placeholder="Set completion date"
              :disabled="false"
              @update:modelValue="$resources.task.setValue.submit({ completed_at: $event })"
            />
            <div class="text-ink-gray-6">Timer</div>
            <div class="space-y-1.5">
              <div class="flex flex-wrap items-center gap-2">
                <span class="font-mono text-base tabular-nums text-ink-gray-9">{{ timerDisplay }}</span>
                <span v-if="timerRunning" class="text-xs font-medium text-ink-green-3">Running</span>
                <Button
                  v-if="!timerRunning"
                  @click="startTimer"
                  :loading="$resources.task.startTimer.loading"
                  :disabled="!timerCanStart"
                  :title="timerCanStart ? 'Start' : 'Timer already stopped for this status'"
                >
                  <template #icon><LucidePlay class="w-4 h-4" /></template>
                </Button>
                <Button
                  v-if="timerRunning"
                  @click="openPausePrompt"
                  title="Pause"
                >
                  <template #icon><LucidePause class="w-4 h-4" /></template>
                </Button>
                <Button
                  v-if="timerRunning"
                  theme="red"
                  @click="stopTimer"
                  :loading="$resources.task.stopTimer.loading"
                  title="Stop"
                >
                  <template #icon><LucideSquare class="w-4 h-4" /></template>
                </Button>
              </div>
            </div>
          </div>
          <div class="grid grid-cols-[6.5rem_minmax(0,1fr)] items-center gap-x-2 gap-y-1.5 content-start">
            <div class="text-ink-gray-6">Assignees</div>
            <div class="space-y-1">
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="uid in assigneeUserIds"
                  :key="uid"
                  class="inline-flex max-w-full items-center gap-1 rounded bg-surface-gray-2 px-2 py-0.5 text-sm text-ink-gray-8"
                >
                  <span class="truncate whitespace-nowrap">{{ $user(uid).full_name }}</span>
                  <button
                    type="button"
                    class="leading-none shrink-0 text-ink-gray-5 hover:text-ink-gray-8"
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
            <div class="text-ink-gray-6">Priority</div>
            <Dropdown :options="priorityOptions">
              <Button class="whitespace-nowrap">
                <template v-if="$resources.task.doc.priority" #prefix>
                  <TaskPriorityIcon :priority="$resources.task.doc.priority" />
                </template>
                {{ $resources.task.doc.priority || 'Set priority' }}
              </Button>
            </Dropdown>
            <div class="text-ink-gray-6">Tags</div>
            <div class="space-y-1">
              <div
                v-for="tag in taskTags"
                :key="tag"
                class="flex items-center justify-between gap-2 px-2 py-0.5 rounded bg-surface-gray-2"
              >
                <div class="flex items-center gap-1.5 min-w-0">
                  <LucideTag class="h-3.5 w-3.5 shrink-0 text-ink-gray-5" />
                  <span class="text-sm truncate text-ink-gray-8">{{ tag }}</span>
                </div>
                <Button variant="ghost" @click="removeTag(tag)" :aria-label="`Remove ${tag}`">
                  <template #icon><LucideTrash2 class="h-3.5 w-3.5" /></template>
                </Button>
              </div>
              <Autocomplete
                placeholder="Add tag"
                :options="tagOptions"
                v-model="tagSelection"
                @update:modelValue="onTagPicked"
                @update:query="fetchTagSuggestions"
              /></div>
            <div class="text-ink-gray-6">Linked Teams</div>
            <div class="space-y-1">
              <div v-if="linkedTeams.length" class="space-y-1">
                <div
                  v-for="team in linkedTeams"
                  :key="team.name"
                  class="flex items-center justify-between gap-2 px-2 py-0.5 rounded bg-surface-gray-2"
                >
                  <span class="text-sm truncate text-ink-gray-8">{{ team.team_title || team.team }}</span>
                  <Button
                    variant="ghost"
                    @click="unlinkTeam(team.team)"
                    :loading="$resources.task.unlinkTeam.loading"
                    :aria-label="`Remove ${team.team_title || team.team}`"
                  >
                    <template #icon>
                      <LucideTrash2 class="w-4 h-4" />
                    </template>
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
          </div>
        </div>
        <TextEditor
          ref="description"
          editor-class="prose-sm max-w-none focus-within:ring-2 focus-within:ring-outline-gray-3 rounded-sm p-0.5 -ml-0.5 min-h-[4rem]"
          placeholder="Description"
          :content="descriptionContent"
          :bubbleMenu="true"
          @blur="saveDescription"
        >
          <!-- Custom toolbar: @mousedown.prevent keeps the editor focused so
               commands apply on the first click (frappe-ui's built-in menus
               blur the editor and swallow the first click). -->
          <template #top>
            <div
              class="mb-1 flex flex-wrap items-center gap-0.5 border-b border-outline-gray-2 pb-1"
              @mousedown.prevent
            >
              <button v-for="b in descriptionToolbar" :key="b.label" type="button"
                class="flex h-7 min-w-[1.75rem] items-center justify-center rounded px-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
                :class="b.isActive() ? 'bg-surface-gray-3 text-ink-gray-9' : ''"
                :title="b.label"
                @click="b.run"
              >{{ b.text }}</button>
            </div>
          </template>
        </TextEditor>
        <ChildTasks
          class="pt-6 mt-8 border-t border-outline-gray-2"
          :parentTaskId="taskId"
          :parentTask="$resources.task.doc"
        />
        <CommentsList class="mt-8 xl:hidden" doctype="GP Task" :name="taskId" />
      </div>
    </div>
    <div
      class="relative hidden group/resize shrink-0 bg-surface-white xl:flex xl:flex-col"
      :style="{ width: `${activityPanelWidth}px` }"
    >
      <button
        type="button"
        class="absolute -left-1.5 top-0 z-20 hidden h-full w-3 cursor-col-resize items-center justify-center focus:outline-none xl:flex"
        aria-label="Resize activity panel"
        @mousedown.prevent="startActivityResize"
      >
        <span
          class="w-px h-full transition bg-outline-gray-2 group-hover/resize:bg-blue-400"
          :class="isResizingActivity ? 'bg-blue-500' : ''"
        ></span>
      </button>
      <div class="flex flex-wrap items-center justify-between gap-x-2 gap-y-2 px-4 py-3 border-b border-outline-gray-2">
        <div class="flex shrink-0 items-center gap-1">
          <button
            v-for="tab in ['Activity', 'Attachments']"
            :key="tab"
            type="button"
            class="whitespace-nowrap rounded-md px-2 py-1.5 text-sm font-semibold"
            :class="
              activityTab === tab
                ? 'bg-surface-gray-2 text-ink-gray-9'
                : 'text-ink-gray-5 hover:text-ink-gray-8'
            "
            @click="activityTab = tab"
          >
            {{ tab }}
          </button>
        </div>
        <div v-if="activityTab === 'Activity'" class="flex items-center gap-2">
          <Dropdown :options="activityFilterOptions">
            <button class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-outline-gray-2 bg-surface-white px-2.5 py-1.5 text-sm font-semibold text-ink-gray-8 shadow-sm hover:bg-surface-gray-1">
              {{ activityFilterLabel }}
              <LucideChevronDown class="h-3.5 w-3.5 text-ink-gray-6" />
            </button>
          </Dropdown>
          <Dropdown :options="activitySortOptions">
            <button class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-sm font-semibold text-ink-gray-8 hover:bg-surface-gray-1">
              {{ activitySortLabel }}
              <LucideChevronDown class="h-3.5 w-3.5 text-ink-gray-6" />
            </button>
          </Dropdown>
          <button
            class="inline-flex items-center rounded-lg p-1.5 text-ink-gray-8 hover:bg-surface-gray-1"
            title="Export activity as CSV"
            @click="exportActivity"
          >
            <LucideDownload class="h-4 w-4 text-ink-gray-6" />
          </button>
        </div>
      </div>
      <div class="flex flex-col flex-1 min-h-0">
        <TaskAttachments v-if="activityTab === 'Attachments'" :taskId="taskId" />
        <CommentsList
          v-else
          doctype="GP Task"
          :name="taskId"
          class="flex-1 min-h-0"
          :filter="activityFilter"
          :sort="activitySort"
          :show-toolbar="false"
          @update:filter="activityFilter = $event"
          @update:sort="activitySort = $event"
        />
      </div>
    </div>
    <Dialog
      v-model="pausePromptOpen"
      :options="{ title: 'Pause timer' }"
    >
      <template #body-content>
        <label class="block mb-1 text-sm text-ink-gray-6">Pause reason (required)</label>
        <textarea
          v-model="pauseReason"
          rows="3"
          placeholder="Why are you pausing?"
          class="w-full px-2 py-1.5 text-sm border rounded bg-surface-white border-outline-gray-2 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
          @keydown.enter.prevent="confirmPause"
        ></textarea>
      </template>
      <template #actions>
        <Button
          variant="solid"
          class="w-full"
          :disabled="!pauseReason.trim()"
          :loading="$resources.task.pauseTimer.loading"
          @click="confirmPause"
        >
          Confirm pause
        </Button>
      </template>
    </Dialog>
    <Dialog v-model="dueHistoryOpen" :options="{ title: 'Due date revisions' }">
      <template #body-content>
        <div v-if="!dueHistory.length" class="text-sm text-ink-gray-5">No revisions yet.</div>
        <ul v-else class="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
          <li v-for="(rev, i) in dueHistory" :key="i" class="text-sm">
            <div class="text-ink-gray-8">
              <span v-if="rev.old_value">{{ formatDue(rev.old_value) }}</span>
              <span v-else class="text-ink-gray-5">None</span>
              →
              <span v-if="rev.new_value" class="font-medium">{{ formatDue(rev.new_value) }}</span>
              <span v-else class="text-ink-gray-5">None</span>
            </div>
            <div v-if="rev.reason" class="text-ink-gray-7">“{{ rev.reason }}”</div>
            <div class="text-xs text-ink-gray-5">
              {{ $user(rev.user).full_name }} · {{ $dayjs(rev.creation).format('DD/MM/YYYY hh:mm A') }}
            </div>
          </li>
        </ul>
      </template>
    </Dialog>
    <Dialog v-model="duePromptOpen" :options="{ title: 'Change due date' }">
      <template #body-content>
        <label class="block mb-1 text-sm text-ink-gray-6">Reason for changing due date (required)</label>
        <textarea
          v-model="dueReason"
          rows="3"
          placeholder="Why is the due date changing?"
          class="w-full px-2 py-1.5 text-sm border rounded bg-surface-white border-outline-gray-2 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
          @keydown.enter.prevent="confirmDueChange"
        ></textarea>
      </template>
      <template #actions>
        <Button
          variant="solid"
          class="w-full"
          :disabled="!dueReason.trim()"
          :loading="$resources.task.changeDueDate.loading"
          @click="confirmDueChange"
        >
          Save due date
        </Button>
      </template>
    </Dialog>
    <Dialog v-model="holdPromptOpen" :options="{ title: 'Put task on hold' }">
      <template #body-content>
        <label class="block mb-1 text-sm text-ink-gray-6">Hold reason (required)</label>
        <textarea
          v-model="holdReason"
          rows="3"
          placeholder="Why is this task on hold?"
          class="w-full px-2 py-1.5 text-sm border rounded bg-surface-white border-outline-gray-2 focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
          @keydown.enter.prevent="confirmHold"
        ></textarea>
      </template>
      <template #actions>
        <Button
          variant="solid"
          class="w-full"
          :disabled="!holdReason.trim()"
          :loading="$resources.task.hold.loading"
          @click="confirmHold"
        >
          Confirm hold
        </Button>
      </template>
    </Dialog>
  </div>
</template>
<script>
import { h } from 'vue'
import TextEditor from '@/components/TextEditor.vue'
import ReadmeEditor from '@/components/ReadmeEditor.vue'
import CommentsArea from '@/components/CommentsArea.vue'
import { focus } from '@/directives'
import { Autocomplete, Dropdown, LoadingText, DatePicker, Dialog, call } from 'frappe-ui'
import CommentsList from '@/components/CommentsList.vue'
import TaskStatusIcon from '@/components/icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/icons/TaskPriorityIcon.vue'
import ChildTasks from '@/components/ChildTasks.vue'
import TaskAttachments from '@/components/TaskAttachments.vue'
import { activeUsers } from '@/data/users'
import { activeTeams } from '@/data/teams'
import { getTeamProjects } from '@/data/projects'

export default {
  name: 'TaskDetail',
  props: {
    taskId: { type: [String, Number], required: true },
    embedded: { type: Boolean, default: false },
  },
  emits: ['close', 'switch-task'],
  directives: { focus },
  resources: {
    parentTask() {
      const parentId = this.$resources.task?.doc?.parent_task
      if (!parentId) return null
      return {
        type: 'document',
        doctype: 'GP Task',
        name: parentId,
        auto: true,
      }
    },
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
          hold: 'hold',
          changeDueDate: 'change_due_date',
          getDueDateHistory: 'get_due_date_history',
          getTimer: 'get_timer',
          startTimer: 'start_timer',
          pauseTimer: 'pause_timer',
          stopTimer: 'stop_timer',
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
          // Seed the editor only when a different task loads — not on save echoes,
          // which would revert in-progress edits (e.g. applying a numbered list).
          const editor = this.$refs.description?.editor
          const isFocused = editor && editor.isFocused
          if (
            String(doc.name) !== String(this.descriptionLoadedFor) ||
            (!isFocused && (doc.description || '') !== this.descriptionContent)
          ) {
            this.descriptionLoadedFor = doc.name
            this.descriptionContent = doc.description || ''
          }
          if (
            ['ProjectTaskDetail', 'Task'].includes(this.$route.name) &&
            Number(this.$route.params.taskId) === doc.name
          ) {
            this.$resources.task.trackVisit.submit()
          }
          this.dueDateBaseline = doc.due_date || null
          this.$resources.task.getLinkedTeams.submit()
          this.refreshTimer()
          this.loadDocTags()
          this.resizeTitle()
        },
      }
    },
  },
  data() {
    return {
      linkedTeam: null,
      assigneeAddSelection: null,
      activityTab: 'Activity',
      activityFilter: 'all',
      activitySort: 'desc',
      activityPanelWidth: 448,
      isResizingActivity: false,
      resizeStartX: 0,
      resizeStartWidth: 448,
      docTags: [],
      tagSelection: null,
      allTagSuggestions: [],
      tagSearchQuery: '',
      descriptionContent: '',
      descriptionLoadedFor: null,
      timerBase: 0,
      timerRunning: false,
      timerCanStart: true,
      timerAnchorMs: 0,
      nowMs: 0,
      timerInterval: null,
      pausePromptOpen: false,
      pauseReason: '',
      holdPromptOpen: false,
      holdReason: '',
      dueHistoryOpen: false,
      dueHistory: [],
      dueDateBaseline: null,
      duePromptOpen: false,
      dueReason: '',
      pendingDueDate: null,
    }
  },
  watch: {
    taskId() {
      this.docTags = []
      this.loadDocTags()
      this.refreshTimer()
    },
    duePromptOpen(open) {
      // Dismissed without confirming → revert the picker to the saved date.
      if (!open && this.pendingDueDate) {
        this.$resources.task.doc.due_date = this.dueDateBaseline
        this.pendingDueDate = null
      }
    },
  },
  created() {
    this.$watch(
      () => this.$resources?.task?.doc?.title,
      () => {
        this.resizeTitle()
      }
    )
    this.$watch(
      () => this.$resources?.task?.doc,
      (doc) => {
        if (doc && String(doc.name) === String(this.taskId)) {
          const editor = this.$refs.description?.editor
          const isFocused = editor && editor.isFocused
          if (
            String(doc.name) !== String(this.descriptionLoadedFor) ||
            (!isFocused && (doc.description || '') !== this.descriptionContent)
          ) {
            this.descriptionLoadedFor = doc.name
            this.descriptionContent = doc.description || ''
          }
        }
      },
      { immediate: true }
    )
  },
  mounted() {
    this.restoreActivityPanelWidth()
    this.loadDocTags()
    this.fetchTagSuggestions('')
    this.resizeTitle()
    this.refreshTimer()
    window.addEventListener('mousemove', this.onActivityResize)
    window.addEventListener('mouseup', this.stopActivityResize)
    window.addEventListener('resize', this.onWindowResize)
    this.timerInterval = setInterval(() => {
      if (this.timerRunning) this.nowMs = Date.now()
    }, 1000)
  },
  beforeUnmount() {
    this.saveDescription() // flush unsaved description on back/navigation
    clearInterval(this.timerInterval)
    window.removeEventListener('mousemove', this.onActivityResize)
    window.removeEventListener('mouseup', this.stopActivityResize)
    window.removeEventListener('resize', this.onWindowResize)
    document.body.classList.remove('select-none', 'cursor-col-resize')
  },
  methods: {
    confirmDeleteTask() {
      this.$dialog({
        title: 'Delete task',
        message: 'Are you sure you want to delete this task?',
        actions: [
          {
            label: 'Delete',
            theme: 'red',
            variant: 'solid',
            onClick: (close) => {
              return this.$resources.task.delete.submit(null, {
                onSuccess: () => {
                  close()
                  if (this.embedded) {
                    this.$emit('close')
                  } else {
                    this.$router.back()
                  }
                },
              })
            },
          },
        ],
      })
    },
    resizeTitle() {
      this.$nextTick(() => {
        const el = this.$refs.titleTextarea
        if (el) {
          el.style.height = 'auto'
          el.style.height = el.scrollHeight + 'px'
        }
      })
    },
    saveDescription() {
      const editor = this.$refs.description?.editor
      if (!editor) return
      // Empty editor -> save "" so a cleared description actually persists.
      const html = editor.isEmpty ? '' : editor.getHTML()
      if (html === (this.$resources.task.doc.description || '')) return // nothing changed
      this.$resources.task.setValue.submit({ description: html })
    },
    restoreActivityPanelWidth() {
      const savedWidth = Number(localStorage.getItem('gameplan_task_activity_width'))
      if (savedWidth) {
        this.activityPanelWidth = this.clampActivityPanelWidth(savedWidth)
        localStorage.setItem('gameplan_task_activity_width', String(this.activityPanelWidth))
      }
    },
    onWindowResize() {
      this.activityPanelWidth = this.clampActivityPanelWidth(this.activityPanelWidth)
    },
    clampActivityPanelWidth(width) {
      const minTaskDetailWidth = 760
      const maxPanelWidth = 720
      const maxWidth = Math.max(420, Math.min(maxPanelWidth, window.innerWidth - minTaskDetailWidth))
      return Math.min(Math.max(width, 360), maxWidth)
    },
    startActivityResize(event) {
      this.isResizingActivity = true
      this.resizeStartX = event.clientX
      this.resizeStartWidth = this.activityPanelWidth
      document.body.classList.add('select-none', 'cursor-col-resize')
    },
    onActivityResize(event) {
      if (!this.isResizingActivity) return
      const delta = this.resizeStartX - event.clientX
      this.activityPanelWidth = this.clampActivityPanelWidth(this.resizeStartWidth + delta)
    },
    stopActivityResize() {
      if (!this.isResizingActivity) return
      this.isResizingActivity = false
      document.body.classList.remove('select-none', 'cursor-col-resize')
      localStorage.setItem('gameplan_task_activity_width', String(this.activityPanelWidth))
    },
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
    refreshTimer() {
      if (!this.taskId || !this.$resources?.task?.getTimer) return
      this.$resources.task.getTimer.submit(null, {
        onSuccess: () => {
          const data = this.$resources.task.getTimer.data || {}
          this.timerBase = data.total_seconds || 0
          this.timerRunning = !!data.running
          this.timerCanStart = data.can_start !== false
          this.timerAnchorMs = Date.now()
          this.nowMs = Date.now()
        },
      })
    },
    startTimer() {
      this.$resources.task.startTimer.submit(null, { onSuccess: () => this.refreshTimer() })
    },
    onDueDateChange(newDate) {
      const old = this.dueDateBaseline
      // Only ask for a reason when an existing due date is being changed to a different one.
      if (old && newDate && old !== newDate) {
        this.pendingDueDate = newDate
        this.dueReason = ''
        this.duePromptOpen = true
        return
      }
      this.saveDueDate(newDate, null)
    },
    saveDueDate(dueDate, reason) {
      const onSuccess = () => {
        this.dueDateBaseline = dueDate || null
      }
      if (reason) {
        this.$resources.task.changeDueDate.submit({ due_date: dueDate, reason }, { onSuccess })
      } else {
        this.$resources.task.setValue.submit({ due_date: dueDate }, { onSuccess })
      }
    },
    confirmDueChange() {
      const reason = this.dueReason.trim()
      if (!reason) return
      this.saveDueDate(this.pendingDueDate, reason)
      this.pendingDueDate = null
      this.duePromptOpen = false
    },
    async exportActivity() {
      const rows = await call('frappe.client.get_list', {
        doctype: 'GP Activity',
        filters: { reference_doctype: 'GP Task', reference_name: this.taskId },
        fields: ['user', 'action', 'data', 'creation', 'pinned'],
        order_by: `creation ${this.activitySort === 'asc' ? 'asc' : 'desc'}`,
        limit_page_length: 0,
      })
      const csvCell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
      const describe = (action, data) => {
        const d = data ? (typeof data === 'string' ? JSON.parse(data) : data) : {}
        if (d.reason) return d.reason
        if (d.field_label) return `${d.field_label}: ${d.old_value ?? '—'} → ${d.new_value ?? '—'}`
        return ''
      }
      const header = ['Time', 'User', 'Action', 'Details', 'Pinned']
      const lines = [header.map(csvCell).join(',')]
      for (const r of rows) {
        lines.push(
          [
            this.$dayjs(r.creation).format('YYYY-MM-DD HH:mm:ss'),
            this.$user(r.user).full_name || r.user,
            r.action,
            describe(r.action, r.data),
            r.pinned ? 'Yes' : 'No',
          ]
            .map(csvCell)
            .join(','),
        )
      }
      const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `task-${this.taskId}-activity.csv`
      a.click()
      URL.revokeObjectURL(url)
    },
    openDueHistory() {
      this.dueHistoryOpen = true
      this.$resources.task.getDueDateHistory.submit(null, {
        onSuccess: () => {
          this.dueHistory = this.$resources.task.getDueDateHistory.data || []
        },
      })
    },
    formatDue(raw) {
      if (!raw) return ''
      const d = new Date(String(raw).replace(' ', 'T'))
      return isNaN(d) ? raw : d.toLocaleDateString()
    },
    openHoldPrompt() {
      this.holdReason = ''
      this.holdPromptOpen = true
    },
    confirmHold() {
      const reason = this.holdReason.trim()
      if (!reason) return
      this.$resources.task.hold.submit(
        { reason },
        {
          onSuccess: () => {
            this.holdPromptOpen = false
            this.holdReason = ''
          },
        },
      )
    },
    openPausePrompt() {
      this.pauseReason = ''
      this.pausePromptOpen = true
    },
    confirmPause() {
      const reason = this.pauseReason.trim()
      if (!reason) return
      this.$resources.task.pauseTimer.submit(
        { reason },
        {
          onSuccess: () => {
            this.pausePromptOpen = false
            this.pauseReason = ''
            this.refreshTimer()
          },
        },
      )
    },
    stopTimer() {
      this.$resources.task.stopTimer.submit(null, {
        onSuccess: () => {
          this.pausePromptOpen = false
          this.pauseReason = ''
          this.refreshTimer()
        },
      })
    },
    formatDuration(totalSeconds) {
      const s = Math.max(0, Math.floor(totalSeconds))
      const hh = String(Math.floor(s / 3600)).padStart(2, '0')
      const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0')
      const ss = String(s % 60).padStart(2, '0')
      return `${hh}:${mm}:${ss}`
    },
    loadDocTags() {
      call('gameplan.gameplan.doctype.gp_task.gp_task.get_task_tags_for_doc', {
        task_id: this.taskId,
      }).then((tags) => {
        this.docTags = tags || []
      })
    },
    fetchTagSuggestions(txt = '') {
      this.tagSearchQuery = txt
      call('gameplan.gameplan.doctype.gp_task.gp_task.get_task_tags', {
        txt,
      }).then((tags) => {
        this.allTagSuggestions = tags || []
      })
    },
    onTagPicked(option) {
      this.tagSelection = null
      if (!option?.value) return
      this.addTag(option.value)
    },
    addTag(tag) {
      tag = tag?.trim()
      if (!tag || this.taskTags.includes(tag)) return
      call('frappe.desk.doctype.tag.tag.add_tag', {
        dt: 'GP Task',
        dn: this.taskId,
        tag,
      }).then(() => {
        this.loadDocTags()
        this.fetchTagSuggestions('')
      })
    },
    removeTag(tag) {
      call('frappe.desk.doctype.tag.tag.remove_tag', {
        dt: 'GP Task',
        dn: this.taskId,
        tag,
      }).then(() => {
        this.loadDocTags()
      })
    },
    openParentTask() {
      const parentId = this.$resources.task.doc.parent_task
      if (this.embedded) {
        this.$emit('switch-task', parentId)
        return
      }
      const parent = this.$resources.parentTask?.doc
      this.$router.push({
        name: parent?.project ? 'ProjectTaskDetail' : 'Task',
        params: { teamId: parent?.team, projectId: parent?.project, taskId: parentId },
      })
    },
    updateRoute() {
      if (this.embedded) return
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
    isAutoCompletion() {
      return ['Done', 'Live'].includes(this.$resources.task.doc?.status)
    },
    completedDate() {
      const raw = this.$resources.task.doc?.completed_at
      if (!raw) return ''
      const d = new Date(raw.replace(' ', 'T'))
      return isNaN(d) ? raw : d.toLocaleDateString()
    },
    timerDisplay() {
      const live = this.timerRunning ? Math.floor((this.nowMs - this.timerAnchorMs) / 1000) : 0
      return this.formatDuration(this.timerBase + live)
    },
    descriptionToolbar() {
      const ed = () => this.$refs.description?.editor
      const chain = () => ed().chain().focus()
      return [
        { label: 'Paragraph', text: 'T', run: () => chain().setParagraph().run(), isActive: () => ed()?.isActive('paragraph') },
        { label: 'Heading 2', text: 'H2', run: () => chain().toggleHeading({ level: 2 }).run(), isActive: () => ed()?.isActive('heading', { level: 2 }) },
        { label: 'Heading 3', text: 'H3', run: () => chain().toggleHeading({ level: 3 }).run(), isActive: () => ed()?.isActive('heading', { level: 3 }) },
        { label: 'Bullet List', text: '•', run: () => chain().toggleBulletList().run(), isActive: () => ed()?.isActive('bulletList') },
        { label: 'Numbered List', text: '1.', run: () => chain().toggleOrderedList().run(), isActive: () => ed()?.isActive('orderedList') },
        { label: 'Quote', text: '❝', run: () => chain().toggleBlockquote().run(), isActive: () => ed()?.isActive('blockquote') },
        { label: 'Code', text: '</>', run: () => chain().toggleCodeBlock().run(), isActive: () => ed()?.isActive('codeBlock') },
        { label: 'Divider', text: '—', run: () => chain().setHorizontalRule().run(), isActive: () => false },
      ]
    },
    activityFilterLabel() {
      return {
        all: 'All',
        comments: 'Comments',
        activity: 'Activity',
      }[this.activityFilter] || 'All'
    },
    activityFilterOptions() {
      return [
        { label: 'All', onClick: () => (this.activityFilter = 'all') },
        { label: 'Comments', onClick: () => (this.activityFilter = 'comments') },
        { label: 'Activity', onClick: () => (this.activityFilter = 'activity') },
      ]
    },
    activitySortLabel() {
      return this.activitySort === 'desc' ? 'Newest' : 'Oldest'
    },
    activitySortOptions() {
      return [
        { label: 'Newest on top', onClick: () => (this.activitySort = 'desc') },
        { label: 'Oldest on top', onClick: () => (this.activitySort = 'asc') },
      ]
    },
    parentTaskTitle() {
      return this.$resources.parentTask?.doc?.title || null
    },
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
      return ['Backlog', 'Todo', 'In Progress', 'Reopen', 'Ready for Testing', 'Hold', 'QA Accepted', 'Live', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Not a Bug', 'Brief Received', 'Ideation', 'Designing', 'Internal Review', 'Stakeholder Review', 'Revisions', 'Finalized', 'Design In Review', 'Design Confirmed'].map((status) => {
        return {
          icon: () => h(TaskStatusIcon, { status }),
          label: status,
          onClick: () => {
            if (status === 'Hold') {
              this.openHoldPrompt()
              return
            }
            this.$resources.task.setValue.submit({ status }, { onSuccess: () => this.refreshTimer() })
          },
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
    taskTypeOptions() {
      return [
        'Task',
        'Feature',
        'Milestone',
        'Improvement',
        'Bug',
        'Event',
        'Form Response',
        'Meeting Note',
        'Request',
        'Approval',
        'Follow-up',
        'Documentation',
        'Support',
      ].map((task_type) => {
        return {
          label: task_type,
          onClick: () => this.$resources.task.setValue.submit({ task_type }),
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
    taskTags() {
      return this.docTags
    },
    tagOptions() {
      const query = (this.tagSearchQuery || '').trim().toLowerCase()
      const available = this.allTagSuggestions.filter((t) => !this.docTags.includes(t))
      const filtered = query
        ? available.filter((t) => t.toLowerCase().includes(query))
        : available
      const options = filtered.map((t) => ({ label: t, value: t }))
      const alreadyExists = this.allTagSuggestions.some((t) => t.toLowerCase() === query)
      if (query && !alreadyExists && !this.docTags.includes(this.tagSearchQuery.trim())) {
        options.push({ label: `Create "${this.tagSearchQuery.trim()}"`, value: this.tagSearchQuery.trim() })
      }
      return options
    },
    canDeleteTask() {
      const task = this.$resources.task.doc
      const user = this.$user('sessionUser')
      return Boolean(
        task &&
          (task.owner === user.name ||
            user.name === 'Administrator' ||
            user.role === 'Gameplan Admin' ||
            user.is_system_manager),
      )
    },
  },
  components: {
    ReadmeEditor,
    TextEditor,
    CommentsArea,
    Autocomplete,
    Dropdown,
    Dialog,
    CommentsList,
    TaskStatusIcon,
    LoadingText,
    TaskPriorityIcon,
    DatePicker,
    ChildTasks,
    TaskAttachments,
  },
}
</script>
