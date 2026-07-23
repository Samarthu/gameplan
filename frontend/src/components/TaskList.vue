<template>
  <div>
    <Teleport to="body">
      <div
        v-if="showFiltersPanel"
        class="fixed z-50 w-[min(56rem,calc(100vw-2rem))] rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-2xl"
        :style="filtersPanelStyle"
        @click.stop
      >
        <div class="mb-4 flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-semibold text-ink-gray-9">Filters</h3>
            <LucideInfo class="h-3.5 w-3.5 text-ink-gray-4" />
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-1 rounded-lg border border-outline-gray-2 px-2.5 py-1.5 text-sm font-medium text-ink-gray-6 hover:bg-surface-gray-2"
            @click="clearAllFilters"
          >
            Clear
          </button>
        </div>

        <div v-if="taskFilters.length" class="space-y-2">
          <div
            v-for="filter in taskFilters"
            :key="filter.id"
            class="relative grid grid-cols-[minmax(8rem,1fr)_minmax(7rem,0.7fr)_minmax(10rem,1.8fr)_2rem] items-center gap-2 rounded-lg bg-surface-gray-1 p-2"
          >
            <select
              v-model="filter.field"
              class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
              @change="resetFilterValue(filter)"
            >
              <option v-for="field in filterFields" :key="field.value" :value="field.value">
                {{ field.label }}
              </option>
            </select>
            <select
              v-model="filter.operator"
              class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
              @change="resetFilterValue(filter)"
            >
              <option v-for="operator in operatorsForFilter(filter)" :key="operator.value" :value="operator.value">
                {{ operator.label }}
              </option>
            </select>
            <template v-if="filterNeedsValue(filter)">
              <div v-if="isMultiValueFilter(filter) && !isLikeFilter(filter) && valueOptionsForFilter(filter).length" class="relative">
                <button
                  type="button"
                  class="flex h-9 w-full items-center justify-between gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-left text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                  @click.stop="toggleFilterValueMenu(filter.id)"
                >
                  <span class="min-w-0 truncate">
                    {{ selectedFilterValueLabel(filter) || 'Select values' }}
                  </span>
                  <LucideChevronDown class="h-4 w-4 shrink-0 text-ink-gray-5" />
                </button>
                <div
                  v-if="openFilterValueMenu === filter.id"
                  class="absolute left-0 top-full z-50 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-white p-1 shadow-lg"
                  @click.stop
                >
                  <button
                    v-for="option in valueOptionsForFilter(filter)"
                    :key="option.value"
                    type="button"
                    class="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-ink-gray-8 hover:bg-surface-gray-2"
                    @click="toggleFilterValue(filter, option.value)"
                  >
                    <span
                      class="grid h-4 w-4 shrink-0 place-items-center rounded-full border"
                      :class="filter.values.includes(option.value) ? 'border-blue-500 bg-blue-500' : 'border-outline-gray-3 bg-surface-white'"
                    >
                      <LucideCheck v-if="filter.values.includes(option.value)" class="h-3 w-3 text-white" />
                    </span>
                    <span class="min-w-0 truncate">{{ option.label }}</span>
                  </button>
                </div>
              </div>
              <select
                v-else-if="!isLikeFilter(filter) && valueOptionsForFilter(filter).length"
                v-model="filter.value"
                class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
              >
                <option value="">Select value</option>
                <option v-for="option in valueOptionsForFilter(filter)" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <input
                v-else
                v-model="filter.value"
                :type="dateFilterFields.includes(filter.field) ? 'date' : 'text'"
                class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                placeholder="Value"
              />
            </template>
            <div v-else class="h-9 rounded-lg border border-outline-gray-2 bg-surface-white px-2 text-sm text-ink-gray-4"></div>
            <Tooltip text="Remove filter">
              <button
                type="button"
                class="grid h-8 w-8 place-items-center rounded-lg text-ink-gray-5 hover:bg-surface-red-1 hover:text-red-500"
                aria-label="Remove filter"
                @click="removeTaskFilter(filter.id)"
              >
                <LucideTrash2 class="h-4 w-4" />
              </button>
            </Tooltip>
          </div>
        </div>
        <div v-else class="rounded-lg bg-surface-gray-1 px-3 py-4 text-sm text-ink-gray-5">
          No filters applied
        </div>

        <div class="relative mt-4 inline-block">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm font-medium text-ink-gray-7 shadow-sm hover:bg-surface-gray-2"
            @click.stop="toggleAddFilterMenu"
          >
            <LucidePlus class="h-4 w-4" />
            Add filter
          </button>
          <div
            v-if="showAddFilterMenu"
            class="absolute left-0 top-full z-50 mt-1 max-h-64 w-56 overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-white p-1 shadow-lg"
            @click.stop
          >
            <button
              v-for="field in filterFields"
              :key="field.value"
              type="button"
              class="flex w-full items-center rounded px-2 py-1.5 text-left text-sm text-ink-gray-8 hover:bg-surface-gray-2"
              @click="addTaskFilterForField(field.value)"
            >
              {{ field.label }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <div v-if="selectedTag" class="mb-3 flex flex-wrap items-center gap-2">
      <button
        class="inline-flex items-center gap-1 rounded-full bg-surface-blue-1 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100"
        @click="selectedTag = null"
      >
        <LucideTag class="h-3.5 w-3.5 shrink-0" />
        {{ selectedTag }}
        <LucideX class="h-3.5 w-3.5" />
      </button>
    </div>

    <KanbanView
      v-if="filteredTasks.length && viewMode === 'kanban'"
      :tasksResource="tasks"
      :kanbanGroups="kanbanGroups"
      :childTasksByParent="childTasksByParent"
      :isSelected="isSelected"
      :toggleTask="toggleTask"
      :taskRoute="taskRoute"
      :assigneeIds="assigneeIds"
      :visibleAssigneeIds="visibleAssigneeIds"
      :assigneeStackSpacingClass="assigneeStackSpacingClass"
      :assigneeHeatClass="assigneeHeatClass"
      :assigneeHeatStyle="assigneeHeatStyle"
      :extraAssigneeCount="extraAssigneeCount"
      :extraAssigneeNames="extraAssigneeNames"
      :removeAssignee="removeAssignee"
      :isTaskOverdue="isTaskOverdue"
      :priorityIconClass="priorityIconClass"
      :statusOptions="statusOptions"
      :taskTypeOptions="taskTypeOptions"
      :kanbanColumnClass="kanbanColumnClass"
      :userOptions="userOptions"
      :setAssignee="setAssignee"
      :priorityOptions="priorityOptions"
      :setDueDate="setDueDate"
      :canDeleteTask="canDeleteTask"
      :confirmDeleteTask="confirmDeleteTask"
      @request-new-task="$emit('request-new-task', $event)"
      @request-hold="requestHold"
    />

    <TeamView
      v-else-if="filteredTasks.length && viewMode === 'team'"
      :tasks="topLevelTasks"
      :assigneeIds="assigneeIds"
      :taskRoute="taskRoute"
      :isTaskOverdue="isTaskOverdue"
      :updateTask="updateTaskField"
      @request-new-task="$emit('request-new-task', $event)"
    />

    <ListView
      v-else-if="filteredTasks.length"
      :tasksResource="tasks"
      :groupedTasks="groupedTasks"
      :compact="compact"
      :columns="columns"
      :isOpen="isOpen"
      :horizontalScrollLeft="horizontalScrollLeft"
      :showColumnsPicker="showColumnsPicker"
      :columnsPickerStyle="columnsPickerStyle"
      :inlinePopover="inlinePopover"
      :inlinePopoverStyle="inlinePopoverStyle"
      :userOptions="userOptions"
      :syncGroupHeaderScroll="syncGroupHeaderScroll"
      :visibleTasksForGroup="visibleTasksForGroup"
      :isGroupFullySelected="isGroupFullySelected"
      :isGroupPartiallySelected="isGroupPartiallySelected"
      :toggleGroup="toggleGroup"
      :isSelected="isSelected"
      :toggleTask="toggleTask"
      :taskRoute="taskRoute"
      :isTaskOverdue="isTaskOverdue"
      :statusOptions="statusOptions"
      :taskTypeOptions="taskTypeOptions"
      :hasChildTasks="hasChildTasks"
      :isChildTasksOpen="isChildTasksOpen"
      :toggleChildTasks="toggleChildTasks"
      :taskDepth="taskDepth"
      :assigneeIds="assigneeIds"
      :assigneeStackSpacingClass="assigneeStackSpacingClass"
      :visibleAssigneeIds="visibleAssigneeIds"
      :assigneeHeatClass="assigneeHeatClass"
      :assigneeHeatStyle="assigneeHeatStyle"
      :extraAssigneeCount="extraAssigneeCount"
      :extraAssigneeNames="extraAssigneeNames"
      :toggleInlinePopover="toggleInlinePopover"
      :setAssignee="setAssignee"
      :removeAssignee="removeAssignee"
      :priorityOptions="priorityOptions"
      :setDueDate="setDueDate"
      :canDeleteTask="canDeleteTask"
      :confirmDeleteTask="confirmDeleteTask"
      :toggleColumn="toggleColumn"
      :toggleColumnsPicker="toggleColumnsPicker"
      @view-task="openTaskDialog"
    />

    <div
      class="flex flex-col items-center py-8 text-base border-2 border-dashed rounded-lg text-ink-gray-5"
      v-else
    >
      {{ tasks.data?.length ? 'No tasks match the selected filters' : 'No tasks' }}
    </div>

    <TaskDetailDialog
      v-model="showTaskDialog"
      :task-id="selectedTaskId"
      @closed="onTaskDialogClosed"
    />

    <Dialog v-model="holdPromptOpen" :options="{ title: 'Put task on hold' }">
      <template #body-content>
        <label class="mb-1 block text-sm text-ink-gray-6">Hold reason (required)</label>
        <textarea
          v-model="holdReason"
          rows="3"
          placeholder="Why is this task on hold?"
          class="w-full rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
          @keydown.enter.prevent="confirmHold"
        ></textarea>
      </template>
      <template #actions>
        <Button
          variant="solid"
          class="w-full"
          :disabled="!holdReason.trim()"
          :loading="holdSubmitting"
          @click="confirmHold"
        >
          Confirm hold
        </Button>
      </template>
    </Dialog>

    <!-- Bulk action bar -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="translate-y-2 opacity-0"
        enter-to-class="translate-y-0 opacity-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="translate-y-0 opacity-100"
        leave-to-class="translate-y-2 opacity-0"
      >
        <div
          v-if="selectedTasks.length > 0"
          class="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-1.5 rounded-xl border border-outline-gray-2 bg-surface-white px-3 py-2 shadow-2xl"
        >
          <span class="mr-1 whitespace-nowrap text-sm font-medium text-ink-gray-7">
            {{ selectedTasks.length }} selected
          </span>
          <div class="w-px h-4 bg-outline-gray-2"></div>

          <!-- Status -->
          <Dropdown :options="bulkStatusOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideCircleDot class="h-3.5 w-3.5" />
              Status
            </button>
          </Dropdown>

          <!-- Type -->
          <Dropdown :options="bulkTaskTypeOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideCircle class="h-3.5 w-3.5" />
              Type
            </button>
          </Dropdown>

          <!-- Priority -->
          <Dropdown :options="bulkPriorityOptions">
            <button class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2">
              <LucideFlag class="h-3.5 w-3.5" />
              Priority
            </button>
          </Dropdown>

          <!-- Assignee -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('assignee')"
            >
              <LucideUserPlus class="h-3.5 w-3.5" />
              Assignee
            </button>
            <div
              v-if="activePopover === 'assignee'"
              class="absolute w-56 p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <Autocomplete
                :options="userOptions"
                placeholder="Assign person..."
                @update:modelValue="bulkAddAssignee"
              />
            </div>
          </div>

          <!-- Tag -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('tag')"
            >
              <LucideTag class="h-3.5 w-3.5" />
              Tag
            </button>
            <div
              v-if="activePopover === 'tag'"
              class="absolute w-56 p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <Autocomplete
                :options="bulkTagOptions"
                placeholder="Add tag..."
                @update:modelValue="bulkAddTag"
              />
              <div v-if="!bulkTagOptions.length" class="px-2 py-1 text-sm text-ink-gray-5">
                No tags available
              </div>
            </div>
          </div>

          <!-- Due Date -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('date')"
            >
              <LucideCalendar class="h-3.5 w-3.5" />
              Due
            </button>
            <div
              v-if="activePopover === 'date'"
              class="absolute p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <input
                type="date"
                class="block px-2 py-1 text-sm border rounded-md border-outline-gray-2 text-ink-gray-9 focus:outline-none focus:ring-1 focus:ring-outline-gray-4"
                @change="bulkSetDueDate($event.target.value)"
              />
            </div>
          </div>

          <!-- Project -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('project')"
            >
              <LucideFolderOpen class="h-3.5 w-3.5" />
              Project
            </button>
            <div
              v-if="activePopover === 'project'"
              class="absolute w-56 p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <Autocomplete
                :options="projectOptions"
                placeholder="Search project..."
                @update:modelValue="bulkSetProject"
              />
            </div>
          </div>

          <!-- Link team -->
          <div class="relative">
            <button
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('link-team')"
            >
              <LucideUsers class="h-3.5 w-3.5" />
              Team
            </button>
            <div
              v-if="activePopover === 'link-team'"
              class="absolute w-56 p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <Autocomplete
                :options="teamOptions"
                placeholder="Link to team..."
                @update:modelValue="bulkLinkTeam"
              />
            </div>
          </div>

          <!-- Copy to project -->
          <div class="relative">
            <Tooltip text="Copy to another project in the same team">
              <button
                type="button"
                class="flex h-8 w-8 items-center justify-center rounded-lg text-ink-gray-7 transition hover:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-40"
                aria-label="Copy selected tasks to project"
                :disabled="!canCopySelectionToProject"
                @click.stop="togglePopover('copy-project')"
              >
                <LucideCopy class="h-4 w-4" />
              </button>
            </Tooltip>
            <div
              v-if="activePopover === 'copy-project'"
              class="absolute w-64 p-2 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white"
            >
              <Autocomplete
                :options="copyProjectOptions"
                placeholder="Copy to project..."
                @update:modelValue="bulkCopyToProject"
              />
              <div v-if="!copyProjectOptions.length" class="px-2 py-1 text-sm text-ink-gray-5">
                No other project in this team
              </div>
            </div>
          </div>

          <!-- Sprint (Move / Copy) -->
          <div class="relative">
            <button
              type="button"
              class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
              @click="togglePopover('sprint')"
            >
              <LucideZap class="h-3.5 w-3.5" />
              Sprint
            </button>
            <div
              v-if="activePopover === 'sprint'"
              class="absolute w-64 mb-2 -translate-x-1/2 border rounded-lg shadow-lg bottom-full left-1/2 border-outline-gray-2 bg-surface-white overflow-hidden"
            >
              <!-- Mode toggle -->
              <div class="flex border-b border-outline-gray-2">
                <button
                  class="flex-1 py-1.5 text-xs font-medium transition"
                  :class="sprintPopoverMode === 'move' ? 'bg-surface-gray-2 text-ink-gray-9' : 'text-ink-gray-5 hover:bg-surface-gray-1'"
                  @click.stop="sprintPopoverMode = 'move'"
                >
                  Move to Sprint
                </button>
                <button
                  class="flex-1 py-1.5 text-xs font-medium transition"
                  :class="sprintPopoverMode === 'copy' ? 'bg-surface-gray-2 text-ink-gray-9' : 'text-ink-gray-5 hover:bg-surface-gray-1'"
                  @click.stop="sprintPopoverMode = 'copy'"
                >
                  Copy to Sprint
                </button>
              </div>
              <div class="p-2">
                <Autocomplete
                  v-if="sprintPopoverMode === 'move'"
                  :options="sprintOptions"
                  placeholder="Select sprint..."
                  @update:modelValue="bulkMoveToSprint"
                />
                <Autocomplete
                  v-else
                  :options="sprintOptionsForTeam"
                  placeholder="Select sprint..."
                  @update:modelValue="bulkCopyToSprint"
                />
                <div
                  v-if="(sprintPopoverMode === 'move' ? sprintOptions : sprintOptionsForTeam).length === 0"
                  class="px-2 py-1 text-sm text-ink-gray-5"
                >
                  No sprints available
                </div>
              </div>
            </div>
          </div>

          <div class="w-px h-4 bg-outline-gray-2"></div>

          <!-- Export to Excel -->
          <div class="relative">
            <Tooltip text="Export selected tasks to Excel">
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-ink-gray-7 transition hover:bg-surface-gray-2"
                @click.stop="toggleExportPopover($event)"
              >
                <LucideSheet class="h-3.5 w-3.5" />
                Export
              </button>
            </Tooltip>
          </div>

          <div class="w-px h-4 bg-outline-gray-2"></div>

          <!-- Delete -->
          <Tooltip text="Delete selected tasks">
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-lg text-red-500 transition hover:bg-surface-red-1"
              aria-label="Delete selected tasks"
              @click="confirmBulkDelete"
            >
              <LucideTrash2 class="h-4 w-4" />
            </button>
          </Tooltip>

          <!-- Clear -->
          <Tooltip text="Clear selection">
            <button
              type="button"
              class="flex h-8 w-8 items-center justify-center rounded-lg text-ink-gray-5 transition hover:bg-surface-gray-2 hover:text-ink-gray-7"
              aria-label="Clear selection"
              @click="clearSelection"
            >
              <LucideX class="h-4 w-4" />
            </button>
          </Tooltip>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <div
        v-if="showExportPopover"
        class="fixed z-[60] overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white shadow-2xl"
        :style="exportPopoverStyle"
        data-export-popover
        @click.stop
      >
        <div class="border-b border-outline-gray-2 px-4 py-3">
          <div class="text-sm font-semibold text-ink-gray-9">Export to Excel</div>
          <div class="mt-0.5 text-xs text-ink-gray-5">
            {{ selectedTasks.length }} task{{ selectedTasks.length === 1 ? '' : 's' }} · choose columns
          </div>
        </div>
        <div class="max-h-48 overflow-y-auto px-4 py-2">
          <label
            v-for="col in exportColumnDefs"
            :key="col.key"
            class="flex items-center gap-2 rounded px-1 py-1.5 text-sm text-ink-gray-8 hover:bg-surface-gray-1"
          >
            <input
              type="checkbox"
              class="h-3.5 w-3.5 rounded border-outline-gray-3 text-ink-gray-9 focus:ring-0"
              :checked="exportColumnSelection[col.key]"
              :disabled="col.required"
              @change="toggleExportColumn(col.key)"
            />
            <span>{{ col.label }}</span>
          </label>
        </div>
        <div class="space-y-2 border-t border-outline-gray-2 px-4 py-3">
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="rounded px-2 py-1 text-xs font-medium text-ink-gray-6 hover:bg-surface-gray-2"
              @click="selectVisibleExportColumns"
            >
              Visible columns
            </button>
            <button
              type="button"
              class="rounded px-2 py-1 text-xs font-medium text-ink-gray-6 hover:bg-surface-gray-2"
              @click="selectAllExportColumns"
            >
              Select all
            </button>
            <button
              type="button"
              class="rounded px-2 py-1 text-xs font-medium text-ink-gray-6 hover:bg-surface-gray-2"
              @click="clearExportColumns"
            >
              Clear
            </button>
          </div>
          <button
            type="button"
            class="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!hasExportColumnsSelected"
            @click="exportSelectedTasks"
          >
            <LucideSheet class="h-4 w-4" />
            Export to Excel
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>
<script>
import { h } from 'vue'
import { Dropdown, Autocomplete, Tooltip, Dialog, call } from 'frappe-ui'
import TaskStatusIcon from './icons/TaskStatusIcon.vue'
import ListView from './ListView.vue'
import KanbanView from './KanbanView.vue'
import TeamView from './TeamView.vue'
import TaskDetailDialog from './TaskDetailDialog.vue'
import { activeProjects } from '@/data/projects'
import { activeTeams } from '@/data/teams'
import { activeUsers, getUser } from '@/data/users'
import { sprints } from '@/data/sprints'
import {
  downloadTasksSpreadsheet,
  getDefaultExportSelection,
  getExportColumnDefs,
} from '@/utils/taskExport'
import { onProjectMerged } from '@/utils/projectMerge'

const COLUMNS_STORAGE_KEY = 'gameplan_task_columns'
const TASK_TYPES = [
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
]

export default {
  name: 'TaskList',
  props: {
    viewMode: {
      type: String,
      default: 'list',
    },
    groupByStatus: {
      type: Boolean,
      default: false,
    },
    listOptions: {
      type: Object,
      default: () => ({}),
    },
    compact: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    let saved = {}
    try {
      saved = JSON.parse(localStorage.getItem(COLUMNS_STORAGE_KEY) || '{}')
    } catch {}
    return {
      isOpen: {
        Backlog: true,
        Todo: true,
        'In Progress': true,
        'Ready for Testing': true,
        'Under Testing': true,
        'Ready to Merge': true,
        Reopen: true,
        Cancelled: true,
        Done: true,
      },
      selectedTasks: [],
      openChildTasks: {},
      horizontalScrollLeft: 0,
      activePopover: null,
      sprintPopoverMode: 'move',
      showColumnsPicker: false,
      columnsPickerStyle: {},
      showFiltersPanel: false,
      filtersPanelStyle: {},
      openFilterValueMenu: null,
      showAddFilterMenu: false,
      showExportPopover: false,
      exportColumnSelection: {},
      exportPopoverStyle: {},
      inlinePopover: { name: null, field: null },
      inlinePopoverStyle: {},
      selectedTag: null,
      searchQuery: '',
      allTags: [],
      taskFilters: [],
      nextFilterId: 1,
      dateFilterFields: ['due_date', 'creation'],
      filterFields: [
        { label: 'Status', value: 'status' },
        { label: 'Tags', value: 'tag' },
        { label: 'Due Date', value: 'due_date' },
        { label: 'Priority', value: 'priority' },
        { label: 'Assignee', value: 'assignee' },
        { label: 'Type', value: 'task_type' },
        { label: 'Project', value: 'project' },
        { label: 'Created By', value: 'owner' },
        { label: 'Date Created', value: 'creation' },
      ],
      filterOperators: [
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not_equals' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not_like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not_in' },
        { label: 'Is', value: 'is' },
      ],
      columns: {
        assignee:   { label: 'Assignee',    visible: saved.assignee   ?? true },
        priority:   { label: 'Priority',    visible: saved.priority   ?? true },
        due_date:   { label: 'Due Date',    visible: saved.due_date   ?? true },
        status:     { label: 'Status',      visible: saved.status     ?? false },
        modified:   { label: 'Modified',    visible: saved.modified   ?? true },
        created_by: { label: 'Created By',  visible: saved.created_by ?? false },
        tags:       { label: 'Tags',        visible: saved.tags       ?? true },
        project:    { label: 'Project',     visible: saved.project    ?? true },
        team:       { label: 'Team',        visible: saved.team       ?? true },
      },
      showTaskDialog: false,
      selectedTaskId: null,
      holdPromptOpen: false,
      holdReason: '',
      holdTaskNames: [],
      holdSubmitting: false,
    }
  },
  watch: {
    selectedTag() {
      this.$resources.tasks.reload()
    },
  },
  mounted() {
    document.addEventListener('click', this.handleOutsideClick)
    this._unsubscribeProjectMerged = onProjectMerged(() => {
      this.tasks?.reload?.()
    })
    call('gameplan.gameplan.doctype.gp_task.gp_task.get_task_tags', { txt: '' }).then((tags) => {
      this.allTags = tags || []
    })
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick)
    this._unsubscribeProjectMerged?.()
  },
  components: {
    Dropdown,
    Autocomplete,
    TaskStatusIcon,
    ListView,
    KanbanView,
    TeamView,
    TaskDetailDialog,
    Dialog,
  },
  resources: {
    tasks() {
      return {
        type: 'list',
        url: 'gameplan.gameplan.doctype.gp_task.gp_task.get_list',
        cache: ['Tasks', this.listOptions],
        doctype: 'GP Task',
        fields: ['*', '_user_tags', 'project.title as project_title', 'team.title as team_title'],
        filters: { ...this.listOptions.filters, ...(this.selectedTag ? { tag: this.selectedTag } : {}) },
        orderBy: this.listOptions.orderBy || 'creation desc',
        pageLength: this.listOptions.pageLength || 1000,
        auto: true,
        realtime: true,
      }
    },
  },
  methods: {
    openTaskDialog(taskId) {
      this.selectedTaskId = String(taskId)
      this.showTaskDialog = true
    },
    onTaskDialogClosed() {
      this.tasks.reload()
    },
    syncGroupHeaderScroll(event) {
      this.horizontalScrollLeft = event.target.scrollLeft
    },
    hasChildTasks(task) {
      return Boolean(this.childTasksByParent[task.name]?.length)
    },
    isChildTasksOpen(taskName) {
      return Boolean(this.openChildTasks[taskName])
    },
    toggleChildTasks(taskName) {
      this.openChildTasks = {
        ...this.openChildTasks,
        [taskName]: !this.openChildTasks[taskName],
      }
    },
    visibleTasksForGroup(tasks) {
      return this.collectVisibleTasks(tasks)
    },
    collectVisibleTasks(tasks, depth = 0, visited = new Set()) {
      const visibleTasks = []
      for (const task of tasks) {
        if (visited.has(task.name)) continue
        visited.add(task.name)
        visibleTasks.push({ ...task, _depth: depth })
        if (this.isChildTasksOpen(task.name)) {
          visibleTasks.push(
            ...this.collectVisibleTasks(
              this.childTasksByParent[task.name] || [],
              depth + 1,
              visited,
            ),
          )
        }
      }
      return visibleTasks
    },
    taskDepth(task) {
      return Number(task._depth || 0)
    },
    taskRoute(task) {
      if (this.$route.name === 'TeamTasks') {
        return {
          name: 'Task',
          params: { taskId: task.name },
        }
      }
      return {
        name: task.project ? 'ProjectTaskDetail' : 'Task',
        params: { teamId: task.team, projectId: task.project, taskId: task.name },
      }
    },
    statusOptions({ onClick, name }) {
      return ['Backlog', 'Todo', 'In Progress', 'Reopen', 'Ready for Testing', 'Hold', 'QA Accepted', 'Live', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Not a Bug', 'Brief Received', 'Ideation', 'Designing', 'Internal Review', 'Stakeholder Review', 'Revisions', 'Finalized', 'Design In Review', 'Design Confirmed'].map((status) => {
        return {
          icon: () => h(TaskStatusIcon, { status }),
          label: status,
          onClick: () => {
            // Moving to Hold requires a reason — route through the hold prompt instead of a plain field write.
            if (status === 'Hold' && name) return this.requestHold(name)
            onClick(status)
          },
        }
      })
    },
    requestHold(name) {
      this.holdTaskNames = [name]
      this.holdReason = ''
      this.holdPromptOpen = true
    },
    requestBulkHold() {
      this.holdTaskNames = [...this.selectedTasks]
      this.holdReason = ''
      this.holdPromptOpen = true
    },
    async confirmHold() {
      const reason = this.holdReason.trim()
      if (!reason || !this.holdTaskNames.length) return
      this.holdSubmitting = true
      try {
        // Sequential: concurrent doc saves collide and leave some tasks unchanged.
        for (const task of this.holdTaskNames) {
          await call('gameplan.gameplan.doctype.gp_task.gp_task.hold_task', { task, reason })
        }
        this.holdPromptOpen = false
        this.clearSelection()
        this.tasks.reload()
      } finally {
        this.holdSubmitting = false
      }
    },
    taskTypeOptions({ onClick }) {
      return TASK_TYPES.map((taskType) => ({
        label: taskType,
        onClick: () => onClick(taskType),
      }))
    },
    toggleColumn(key) {
      this.columns[key].visible = !this.columns[key].visible
      const toSave = {}
      for (const [k, v] of Object.entries(this.columns)) toSave[k] = v.visible
      localStorage.setItem(COLUMNS_STORAGE_KEY, JSON.stringify(toSave))
    },
    toggleColumnsPicker(event) {
      if (!this.showColumnsPicker && event?.currentTarget) {
        const rect = event.currentTarget.getBoundingClientRect()
        this.columnsPickerStyle = {
          top: `${rect.bottom + 4}px`,
          right: `${Math.max(window.innerWidth - rect.right, 8)}px`,
        }
      }
      this.showColumnsPicker = !this.showColumnsPicker
    },
    handleOutsideClick(e) {
      if (this.showColumnsPicker) {
        this.showColumnsPicker = false
      }
      if (this.showFiltersPanel) {
        this.showFiltersPanel = false
      }
      if (this.openFilterValueMenu) {
        this.openFilterValueMenu = null
      }
      if (this.showAddFilterMenu) {
        this.showAddFilterMenu = false
      }
      if (this.showExportPopover && !e.target.closest('[data-export-popover]')) {
        this.showExportPopover = false
      }
      if (this.inlinePopover.name) {
        this.inlinePopover = { name: null, field: null }
      }
    },
    toggleExportPopover(event) {
      this.activePopover = null
      const opening = !this.showExportPopover
      if (opening) {
        this.initExportColumnSelection()
        const rect = event?.currentTarget?.getBoundingClientRect()
        if (rect) {
          const width = 320
          const left = Math.min(
            Math.max(rect.left + rect.width / 2 - width / 2, 12),
            window.innerWidth - width - 12,
          )
          const bottom = window.innerHeight - rect.top + 12
          this.exportPopoverStyle = {
            left: `${left}px`,
            bottom: `${bottom}px`,
            width: `${width}px`,
          }
        }
      }
      this.showExportPopover = opening
    },
    initExportColumnSelection() {
      const visibility = {}
      for (const [key, col] of Object.entries(this.columns)) {
        visibility[key] = col.visible
      }
      this.exportColumnSelection = getDefaultExportSelection(visibility)
    },
    toggleExportColumn(key) {
      const col = this.exportColumnDefs.find((c) => c.key === key)
      if (col?.required) return
      this.exportColumnSelection = {
        ...this.exportColumnSelection,
        [key]: !this.exportColumnSelection[key],
      }
    },
    selectAllExportColumns() {
      const selection = {}
      for (const col of this.exportColumnDefs) {
        selection[col.key] = true
      }
      this.exportColumnSelection = selection
    },
    selectVisibleExportColumns() {
      this.initExportColumnSelection()
    },
    clearExportColumns() {
      const selection = {}
      for (const col of this.exportColumnDefs) {
        selection[col.key] = Boolean(col.required)
      }
      this.exportColumnSelection = selection
    },
    exportSelectedTasks() {
      const columnKeys = this.exportColumnDefs
        .filter((col) => this.exportColumnSelection[col.key])
        .map((col) => col.key)
      if (!columnKeys.length || !this.selectedTaskDocs.length) return

      downloadTasksSpreadsheet(this.selectedTaskDocs, columnKeys, {
        getUser,
        dayjs: this.$dayjs,
      })
      this.showExportPopover = false
    },
    toggleFiltersPanel(event) {
      if (!this.showFiltersPanel && event?.currentTarget) {
        const rect = event.currentTarget.getBoundingClientRect()
        this.filtersPanelStyle = {
          top: `${rect.bottom + 8}px`,
          right: `${Math.max(window.innerWidth - rect.right, 16)}px`,
        }
      }
      this.showFiltersPanel = !this.showFiltersPanel
      if (!this.showFiltersPanel) {
        this.openFilterValueMenu = null
      }
    },
    toggleAddFilterMenu() {
      this.showAddFilterMenu = !this.showAddFilterMenu
    },
    addTaskFilterForField(field) {
      this.taskFilters.push({
        id: this.nextFilterId++,
        field,
        operator: 'equals',
        value: '',
        values: [],
      })
      this.showAddFilterMenu = false
    },
    removeTaskFilter(id) {
      this.taskFilters = this.taskFilters.filter((filter) => filter.id !== id)
      if (this.openFilterValueMenu === id) {
        this.openFilterValueMenu = null
      }
    },
    clearAllFilters() {
      this.taskFilters = []
      this.selectedTag = null
      this.openFilterValueMenu = null
      this.showAddFilterMenu = false
    },
    resetFilterValue(filter) {
      if (!this.operatorsForFilter(filter).some((operator) => operator.value === filter.operator)) {
        filter.operator = 'equals'
      }
      filter.value = ''
      filter.values = []
      if (!this.filterNeedsValue(filter)) {
        filter.value = ''
      }
    },
    operatorsForFilter(filter) {
      if (this.dateFilterFields.includes(filter.field)) {
        return this.filterOperators.filter((operator) => ['equals', 'not_equals', 'in', 'not_in', 'is'].includes(operator.value))
      }
      return this.filterOperators
    },
    filterNeedsValue(filter) {
      return filter.operator !== 'is'
    },
    isMultiValueFilter(filter) {
      return ['in', 'not_in'].includes(filter.operator)
    },
    isLikeFilter(filter) {
      return ['like', 'not_like'].includes(filter.operator)
    },
    toggleFilterValueMenu(id) {
      this.openFilterValueMenu = this.openFilterValueMenu === id ? null : id
    },
    toggleFilterValue(filter, value) {
      if (!Array.isArray(filter.values)) {
        filter.values = []
      }
      if (filter.values.includes(value)) {
        filter.values = filter.values.filter((item) => item !== value)
      } else {
        filter.values = [...filter.values, value]
      }
    },
    selectedFilterValueLabel(filter) {
      if (!Array.isArray(filter.values) || !filter.values.length) return ''
      const labelsByValue = new Map(this.valueOptionsForFilter(filter).map((option) => [option.value, option.label]))
      const labels = filter.values.map((value) => labelsByValue.get(value) || value)
      if (labels.length <= 2) return labels.join(', ')
      return `${labels.slice(0, 2).join(', ')} +${labels.length - 2}`
    },
    valueOptionsForFilter(filter) {
      const options = {
        status: ['Backlog', 'Todo', 'In Progress', 'Reopen', 'Ready for Testing', 'Hold', 'QA Accepted', 'Live', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Not a Bug', 'Brief Received', 'Ideation', 'Designing', 'Internal Review', 'Stakeholder Review', 'Revisions', 'Finalized', 'Design In Review', 'Design Confirmed'].map((value) => ({ label: value, value })),
        priority: ['Urgent', 'High', 'Medium', 'Low'].map((value) => ({ label: value, value })),
        task_type: TASK_TYPES.map((value) => ({ label: value, value })),
        tag: this.allTags.map((value) => ({ label: value, value })),
        assignee: this.userOptions,
        owner: this.userOptions,
        project: this.projectOptions,
      }
      return options[filter.field] || []
    },
    taskValueForFilter(task, field) {
      if (field === 'assignee') return this.assigneeIds(task)
      if (field === 'tag') return this.parseTags(task._user_tags)
      return task[field]
    },
    taskMatchesFilter(task, filter) {
      if (!filter.field || !filter.operator) return true
      const rawValue = this.taskValueForFilter(task, filter.field)
      const hasValue = Array.isArray(rawValue)
        ? rawValue.length > 0
        : rawValue !== null && rawValue !== undefined && String(rawValue).trim() !== ''

      if (filter.operator === 'is') return hasValue
      const expectedList = this.expectedValuesForFilter(filter)
      if (!this.filterNeedsValue(filter) || !expectedList.length) return true

      const expected = expectedList[0] || ''
      const values = Array.isArray(rawValue)
        ? rawValue.map((value) => String(value).toLowerCase())
        : [String(rawValue || '').toLowerCase()]

      if (this.dateFilterFields.includes(filter.field)) {
        const actualDate = rawValue ? this.$dayjs(rawValue).startOf('day') : null
        const expectedDate = this.$dayjs(filter.value).startOf('day')
        if (!actualDate?.isValid?.() || !expectedDate.isValid()) return true
        if (filter.operator === 'equals') return actualDate.isSame(expectedDate)
        if (filter.operator === 'not_equals') return !actualDate.isSame(expectedDate)
        if (filter.operator === 'in') return expectedList.some((value) => actualDate.isSame(this.$dayjs(value).startOf('day')))
        if (filter.operator === 'not_in') return expectedList.every((value) => !actualDate.isSame(this.$dayjs(value).startOf('day')))
      }

      if (filter.operator === 'equals') return values.includes(expected)
      if (filter.operator === 'not_equals') return !values.includes(expected)
      if (filter.operator === 'like') return values.some((value) => value.includes(expected))
      if (filter.operator === 'not_like') return values.every((value) => !value.includes(expected))
      if (filter.operator === 'in') return values.some((value) => expectedList.includes(value))
      if (filter.operator === 'not_in') return values.every((value) => !expectedList.includes(value))
      return true
    },
    expectedValuesForFilter(filter) {
      if (this.isMultiValueFilter(filter) && Array.isArray(filter.values) && filter.values.length) {
        return filter.values.map((value) => String(value).trim().toLowerCase()).filter(Boolean)
      }
      return String(filter.value || '')
        .split(',')
        .map((value) => value.trim().toLowerCase())
        .filter(Boolean)
    },
    toggleInlinePopover(taskName, field, event) {
      if (this.inlinePopover.name === taskName && this.inlinePopover.field === field) {
        this.inlinePopover = { name: null, field: null }
      } else {
        // ponytail: fixed positioning so popovers escape the overflow-x-auto list
        // container, which otherwise scrolls/clips when the list is short
        const rect = event?.currentTarget?.getBoundingClientRect()
        if (rect) {
          this.inlinePopoverStyle = {
            top: `${rect.bottom + 4}px`,
            left: `${Math.min(Math.max(rect.left, 8), window.innerWidth - 240)}px`,
          }
        }
        this.inlinePopover = { name: taskName, field }
      }
    },
    setDueDate(task, date) {
      this.inlinePopover = { name: null, field: null }
      this.tasks.setValue.submit({ name: task.name, due_date: date || null })
    },
    updateTaskField(task, field, value) {
      this.tasks.setValue.submit({ name: task.name, [field]: value })
    },
    setAssignee(task, option) {
      if (!option) return
      this.inlinePopover = { name: null, field: null }
      const existing = this.assigneeIds(task)
      if (existing.includes(option.value)) return
      const merged = [...existing, option.value]
      this.tasks.setValue.submit({
        name: task.name,
        assignees: merged.map((user) => ({ user })),
      })
    },
    removeAssignee(task, user) {
      const remaining = this.assigneeIds(task).filter((id) => id !== user)
      this.inlinePopover = { name: null, field: null }
      this.tasks.setValue.submit({
        name: task.name,
        assignees: remaining.map((user) => ({ user })),
      })
    },
    priorityOptions(task) {
      return ['Urgent', 'High', 'Medium', 'Low'].map((p) => ({
        label: p,
        onClick: () => this.tasks.setValue.submit({ name: task.name, priority: p }),
      }))
    },
    priorityIconClass(priority) {
      return {
        Urgent: 'text-red-600',
        High: 'text-red-500',
        Medium: 'text-amber-500',
        Low: 'text-ink-gray-5',
      }[priority] || 'text-ink-gray-5'
    },
    kanbanColumnClass(status) {
      return {
        Backlog: 'bg-surface-gray-1',
        Todo: 'bg-amber-50',
        'In Progress': 'bg-pink-50',
        'Ready for Testing': 'bg-indigo-50',
        'Under Testing': 'bg-surface-blue-1',
        'Ready to Merge': 'bg-green-50',
        Done: 'bg-green-50',
        Cancelled: 'bg-surface-red-1',
        Reopen: 'bg-orange-50',
      }[status] || 'bg-surface-gray-1'
    },

    // Depth in the parent_task tree (root = 0), used to delete children first.
    taskDepth(name) {
      const byName = {}
      for (const t of this.tasks.data || []) byName[t.name] = t
      let depth = 0
      let cur = byName[name]
      const seen = new Set()
      while (cur?.parent_task && byName[cur.parent_task] && !seen.has(cur.name)) {
        seen.add(cur.name)
        depth++
        cur = byName[cur.parent_task]
      }
      return depth
    },
    // Selection helpers
    isSelected(name) {
      return this.selectedTasks.includes(name)
    },
    descendantNames(name) {
      // All subtask names under `name`, recursively (children, grandchildren, …).
      const out = []
      const stack = [name]
      const all = this.filteredTasks
      while (stack.length) {
        const parent = String(stack.pop())
        for (const t of all) {
          if (t.parent_task != null && String(t.parent_task) === parent && !out.includes(t.name)) {
            out.push(t.name)
            stack.push(t.name)
          }
        }
      }
      return out
    },
    toggleTask(name) {
      const selecting = !this.isSelected(name)
      // Cascade to subtasks so selecting a parent selects its whole subtree too.
      const names = [name, ...this.descendantNames(name)]
      for (const n of names) {
        const idx = this.selectedTasks.indexOf(n)
        if (selecting && idx === -1) this.selectedTasks.push(n)
        else if (!selecting && idx > -1) this.selectedTasks.splice(idx, 1)
      }
    },
    isGroupFullySelected(group) {
      return group.tasks.length > 0 && group.tasks.every((t) => this.isSelected(t.name))
    },
    isGroupPartiallySelected(group) {
      return group.tasks.some((t) => this.isSelected(t.name)) && !this.isGroupFullySelected(group)
    },
    toggleGroup(group) {
      // Cascade to subtasks too (children may live in a different status group).
      const names = new Set()
      group.tasks.forEach((t) => {
        names.add(t.name)
        this.descendantNames(t.name).forEach((n) => names.add(n))
      })
      if (this.isGroupFullySelected(group)) {
        names.forEach((n) => {
          const idx = this.selectedTasks.indexOf(n)
          if (idx > -1) this.selectedTasks.splice(idx, 1)
        })
      } else {
        names.forEach((n) => {
          if (!this.isSelected(n)) this.selectedTasks.push(n)
        })
      }
    },
    clearSelection() {
      this.selectedTasks = []
      this.activePopover = null
      this.showExportPopover = false
    },
    togglePopover(name) {
      this.showExportPopover = false
      if (name === 'copy-project' && !this.canCopySelectionToProject) {
        this.$dialog({
          title: 'Cannot copy selection',
          message: 'Select tasks from one team to copy them to another project in that same team.',
        })
        return
      }
      const closing = this.activePopover === name
      this.activePopover = closing ? null : name
      if (closing || name !== 'sprint') this.sprintPopoverMode = 'move'
    },

    // Bulk actions
    async bulkUpdate(field, value) {
      for (const name of this.selectedTasks) {
        await this.tasks.setValue.submit({ name, [field]: value })
      }
      this.clearSelection()
      this.tasks.reload()
    },
    bulkSetDueDate(date) {
      this.activePopover = null
      this.bulkUpdate('due_date', date)
    },
    bulkSetProject(option) {
      if (!option) return
      this.activePopover = null
      this.bulkUpdate('project', option.value)
    },
    async bulkLinkTeam(option) {
      if (!option) return
      this.activePopover = null
      for (const name of this.selectedTasks) {
        await call('gameplan.gameplan.doctype.gp_task.gp_task.link_task_to_team', {
          task: name,
          team: option.value,
        })
      }
      this.clearSelection()
      this.tasks.reload()
    },
    async bulkAddAssignee(option) {
      if (!option) return
      this.activePopover = null
      for (const task of this.selectedTaskDocs) {
        const existing = this.assigneeIds(task)
        if (existing.includes(option.value)) continue
        await this.tasks.setValue.submit({
          name: task.name,
          assignees: [...existing, option.value].map((user) => ({ user })),
        })
      }
      this.clearSelection()
      this.tasks.reload()
    },
    async bulkAddTag(option) {
      if (!option) return
      this.activePopover = null
      for (const name of this.selectedTasks) {
        await call('frappe.desk.doctype.tag.tag.add_tag', { tag: option.value, dt: 'GP Task', dn: name })
      }
      this.clearSelection()
      this.tasks.reload()
    },
    async bulkCopyToProject(option) {
      if (!option) return
      this.activePopover = null
      for (const task of this.selectedTaskDocs) {
        const newTask = await call('frappe.client.insert', {
          doc: {
            doctype: 'GP Task',
            title: task.title,
            description: task.description,
            start_date: task.start_date || null,
            due_date: task.due_date || null,
            task_type: task.task_type || 'Task',
            status: task.status || 'Backlog',
            priority: task.priority || null,
            project: option.value,
            team: this.copyTargetTeam,
            assignees: this.assigneeIds(task).map((user) => ({ user })),
            _user_tags: task._user_tags || null,
          },
        })
        const tags = this.parseTags(task._user_tags)
        for (const tag of tags) {
          await call('frappe.desk.doctype.tag.tag.add_tag', {
            tag,
            dt: 'GP Task',
            dn: newTask.name,
          })
        }
      }
      this.clearSelection()
      this.tasks.reload()
    },
    async bulkMoveToSprint(option) {
      if (!option) return
      this.activePopover = null
      // Moving into a sprint detaches the task from its project so it no longer
      // shows up in the project's task list.
      for (const name of this.selectedTasks) {
        await this.tasks.setValue.submit({ name, sprint: option.value, project: null })
      }
      this.clearSelection()
      this.tasks.reload()
    },
    async bulkCopyToSprint(option) {
      if (!option) return
      this.activePopover = null
      for (const task of this.selectedTaskDocs) {
        const newTask = await call('frappe.client.insert', {
          doc: {
            doctype: 'GP Task',
            title: task.title,
            description: task.description,
            start_date: task.start_date || null,
            due_date: task.due_date || null,
            task_type: task.task_type || 'Task',
            status: task.status || 'Backlog',
            priority: task.priority || null,
            project: null,
            team: task.team || null,
            sprint: option.value,
            assignees: this.assigneeIds(task).map((user) => ({ user })),
          },
        })
        const tags = this.parseTags(task._user_tags)
        for (const tag of tags) {
          await call('frappe.desk.doctype.tag.tag.add_tag', {
            tag,
            dt: 'GP Task',
            dn: newTask.name,
          })
        }
      }
      this.clearSelection()
      this.tasks.reload()
    },
    canDeleteTask(task) {
      const user = this.$user('sessionUser')
      return (
        task.owner === user.name ||
        user.name === 'Administrator' ||
        user.role === 'Gameplan Admin' ||
        user.is_system_manager
      )
    },
    // A task linked to both a project and a sprint only loses its sprint link
    // on delete; the task itself is deleted only when one of the links is absent.
    shouldUnlinkInsteadOfDelete(task) {
      return Boolean(task.project && task.sprint)
    },
    async deleteOrUnlink(task) {
      if (this.shouldUnlinkInsteadOfDelete(task)) {
        await this.tasks.setValue.submit({ name: task.name, sprint: '' })
      } else {
        await this.tasks.delete.submit(task.name)
      }
    },
    confirmDeleteTask(task) {
      const unlink = this.shouldUnlinkInsteadOfDelete(task)
      this.$dialog({
        title: unlink ? 'Remove sprint link' : 'Delete task',
        message: unlink
          ? 'This task is linked to both a project and a sprint, so only the sprint link will be removed (not deleted).'
          : 'Are you sure you want to delete this task?',
        actions: [
          {
            label: unlink ? 'Remove link' : 'Delete',
            theme: 'red',
            variant: 'solid',
            onClick: async (close) => {
              await this.deleteOrUnlink(task)
              close()
              this.selectedTasks = this.selectedTasks.filter((name) => name !== task.name)
              this.tasks.reload()
            },
          },
        ],
      })
    },
    confirmBulkDelete() {
      const deletableTasks = this.selectedTaskDocs.filter((task) => this.canDeleteTask(task))
      const skippedCount = this.selectedTasks.length - deletableTasks.length

      if (!deletableTasks.length) {
        this.$dialog({
          title: 'Cannot delete tasks',
          message: 'You do not have permission to delete the selected tasks.',
        })
        return
      }

      const taskLabel = deletableTasks.length === 1 ? 'task' : 'tasks'
      const skippedMessage = skippedCount
        ? ` ${skippedCount} selected ${skippedCount === 1 ? 'task is' : 'tasks are'} not deletable and will be skipped.`
        : ''
      const unlinkCount = deletableTasks.filter((t) => this.shouldUnlinkInsteadOfDelete(t)).length
      const unlinkMessage = unlinkCount
        ? ` ${unlinkCount} ${unlinkCount === 1 ? 'task is' : 'tasks are'} linked elsewhere and will only lose the sprint link instead of being deleted.`
        : ''

      this.$dialog({
        title: `Delete ${deletableTasks.length} ${taskLabel}`,
        message: `Are you sure you want to delete ${deletableTasks.length} selected ${taskLabel}?${unlinkMessage}${skippedMessage}`,
        actions: [
          {
            label: 'Delete',
            theme: 'red',
            variant: 'solid',
            onClick: async (close) => {
              // Delete deepest-first so a child is removed before its parent,
              // otherwise Frappe's link check blocks deleting the parent.
              const byDepth = [...deletableTasks].sort(
                (a, b) => this.taskDepth(b.name) - this.taskDepth(a.name),
              )
              const errors = []
              for (const task of byDepth) {
                try {
                  await this.deleteOrUnlink(task)
                } catch (e) {
                  const raw = e?.messages?.[0] || e?.message || `Failed to delete ${task.title}`
                  errors.push(raw.replace(/<[^>]+>/g, ''))
                }
              }
              close()
              this.clearSelection()
              this.tasks.reload()
              if (errors.length) {
                this.$dialog({ title: 'Some tasks could not be deleted', message: errors.join('\n') })
              }
            },
          },
        ],
      })
    },

    normalizeUserIdList(val) {
      if (val == null) return []
      if (Array.isArray(val)) return val.filter(Boolean)
      if (typeof val === 'string') {
        const s = val.trim()
        if (!s) return []
        if (s.startsWith('[')) {
          try {
            const p = JSON.parse(s)
            return Array.isArray(p) ? p.filter(Boolean) : []
          } catch {
            return []
          }
        }
        return [s]
      }
      return []
    },
    userIdsFromAssigneesChild(task) {
      const rows = task.assignees
      if (!Array.isArray(rows) || !rows.length) return []
      return rows.map((r) => (typeof r === 'object' && r ? r.user : null)).filter(Boolean)
    },
    assigneeIds(task) {
      const seen = new Set()
      const out = []
      const add = (id) => {
        if (!id || seen.has(id)) return
        seen.add(id)
        out.push(id)
      }
      for (const u of this.userIdsFromAssigneesChild(task)) add(u)
      for (const u of this.normalizeUserIdList(task.assignee_users)) add(u)
      add(task.assigned_to)
      return out
    },
    assigneeStackSpacingClass(task) {
      const n = this.assigneeIds(task).length
      if (n <= 2) return 'gap-1'
      return '-space-x-1.5'
    },
    visibleAssigneeIds(task) {
      return this.assigneeIds(task).slice(0, 3)
    },
    assigneeHeatClass(user) {
      return 'text-white shadow-sm'
    },
    assigneeHeatStyle(user) {
      const seed = `${this.$user(user).full_name || ''}:${user || ''}`
      const palette = [
        { bg: '#b91c1c', ring: '#7f1d1d' },
        { bg: '#c2410c', ring: '#7c2d12' },
        { bg: '#a16207', ring: '#713f12' },
        { bg: '#15803d', ring: '#14532d' },
        { bg: '#047857', ring: '#064e3b' },
        { bg: '#0369a1', ring: '#0c4a6e' },
        { bg: '#1d4ed8', ring: '#1e3a8a' },
        { bg: '#4338ca', ring: '#312e81' },
        { bg: '#7e22ce', ring: '#581c87' },
        { bg: '#be185d', ring: '#831843' },
      ]
      const color = palette[this.hashStringToIndex(seed, palette.length)]
      return {
        backgroundColor: color.bg,
        borderColor: '#fff',
        '--tw-ring-color': color.ring,
      }
    },
    hashStringToIndex(value, length) {
      let hash = 0
      for (let i = 0; i < value.length; i++) {
        hash = (hash << 5) - hash + value.charCodeAt(i)
        hash |= 0
      }
      return Math.abs(hash) % length
    },
    extraAssigneeCount(task) {
      const n = this.assigneeIds(task).length
      return n > 3 ? n - 3 : 0
    },
    extraAssigneeNames(task) {
      return this.assigneeIds(task)
        .slice(3)
        .map((id) => this.$user(id).full_name)
        .filter(Boolean)
        .join(', ')
    },
    parseTags(tags) {
      if (!tags) return []
      return String(tags)
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean)
    },
    isTaskOverdue(task) {
      if (!task.due_date) return false
      if (task.status === 'Done' || task.status === 'Cancelled') return false
      const due = this.$dayjs(task.due_date).startOf('day')
      const today = this.$dayjs().startOf('day')
      return due.isBefore(today)
    },
  },
  computed: {
    tasks() {
      return this.$resources.tasks
    },
    activeFilterCount() {
      return this.taskFilters.filter((filter) => {
        return !this.filterNeedsValue(filter) || this.expectedValuesForFilter(filter).length
      }).length + (this.selectedTag ? 1 : 0)
    },
    filteredTasks() {
      const query = this.searchQuery.toLowerCase()
      return (this.tasks.data || []).filter((task) => {
        if (query) {
          const title = (task.title || '').toLowerCase()
          // description is HTML — strip tags before matching
          const description = (task.description || '').replace(/<[^>]*>/g, ' ').toLowerCase()
          if (!title.includes(query) && !description.includes(query)) return false
        }
        return this.taskFilters.every((filter) => this.taskMatchesFilter(task, filter))
      })
    },
    teamOptions() {
      return activeTeams.value.map((t) => ({
        label: t.title,
        value: t.name,
      }))
    },
    projectOptions() {
      return activeProjects.value.map((p) => ({
        label: p.title,
        value: p.name,
      }))
    },
    selectedTaskTeams() {
      const teams = new Set()
      for (const task of this.selectedTaskDocs) {
        const project = activeProjects.value.find((p) => p.name === task.project)
        const team = task.team || project?.team
        if (team) teams.add(team)
      }
      return [...teams]
    },
    selectedTaskProjectNames() {
      return new Set(this.selectedTaskDocs.map((task) => task.project).filter(Boolean))
    },
    canCopySelectionToProject() {
      return this.selectedTaskDocs.length > 0 && this.selectedTaskTeams.length === 1
    },
    copyTargetTeam() {
      return this.selectedTaskTeams[0] || null
    },
    copyProjectOptions() {
      if (!this.canCopySelectionToProject) return []
      return activeProjects.value
        .filter((project) => {
          return (
            project.team === this.copyTargetTeam &&
            !this.selectedTaskProjectNames.has(project.name)
          )
        })
        .map((project) => ({
          label: project.title,
          value: project.name,
        }))
    },
    sprintOptions() {
      return (sprints.data || []).map((s) => ({
        label: s.title,
        value: s.name,
        description: s.status,
      }))
    },
    sprintOptionsForTeam() {
      if (!this.copyTargetTeam) return this.sprintOptions
      return (sprints.data || [])
        .filter((s) => s.team === this.copyTargetTeam)
        .map((s) => ({ label: s.title, value: s.name, description: s.status }))
    },
    userOptions() {
      return activeUsers.value.map((u) => ({
        label: u.full_name || u.name,
        value: u.name,
      }))
    },
    selectedTaskDocs() {
      const selected = new Set(this.selectedTasks)
      return (this.tasks.data || []).filter((task) => selected.has(task.name))
    },
    exportColumnDefs() {
      return getExportColumnDefs()
    },
    hasExportColumnsSelected() {
      return this.exportColumnDefs.some((col) => this.exportColumnSelection[col.key])
    },
    bulkStatusOptions() {
      return this.statusOptions({
        onClick: (status) => {
          if (status === 'Hold') return this.requestBulkHold()
          this.bulkUpdate('status', status)
        },
      })
    },
    bulkTaskTypeOptions() {
      return this.taskTypeOptions({ onClick: (task_type) => this.bulkUpdate('task_type', task_type) })
    },
    bulkTagOptions() {
      return this.allTags.map((tag) => ({ label: tag, value: tag }))
    },
    bulkPriorityOptions() {
      return [
        { label: 'Urgent', onClick: () => this.bulkUpdate('priority', 'Urgent') },
        { label: 'High',   onClick: () => this.bulkUpdate('priority', 'High') },
        { label: 'Medium', onClick: () => this.bulkUpdate('priority', 'Medium') },
        { label: 'Low',    onClick: () => this.bulkUpdate('priority', 'Low') },
      ]
    },
    filterOptions() {
      const tagOptions = this.allTags.map((tag) => ({
        label: this.selectedTag === tag ? `${tag} selected` : tag,
        onClick: () => {
          this.selectedTag = this.selectedTag === tag ? null : tag
        },
      }))

      if (this.selectedTag) {
        return [
          { label: 'Clear tag filter', onClick: () => (this.selectedTag = null) },
          ...tagOptions,
        ]
      }

      return tagOptions
    },
    groupedTasks() {
      if (!this.groupByStatus) {
        return [{ id: 'all', title: '', tasks: this.topLevelTasks }]
      }
      return ['Backlog', 'Todo', 'In Progress', 'Ready to Merge', 'Ready for Testing', 'Under Testing', 'QA Accepted', 'Done', 'Live', 'Reopen', 'Hold', 'Cancelled', 'Not a Bug', 'Brief Received', 'Ideation', 'Designing', 'Internal Review', 'Stakeholder Review', 'Revisions', 'Finalized', 'Design In Review', 'Design Confirmed'].map((status) => {
        return {
          id: status,
          title: status,
          tasks: this.tasksByStatus[status] || [],
        }
      })
    },
    kanbanGroups() {
      return ['Backlog', 'Todo', 'In Progress', 'Reopen', 'Ready for Testing', 'Hold', 'QA Accepted', 'Live', 'Under Testing', 'Ready to Merge', 'Done', 'Cancelled', 'Not a Bug', 'Brief Received', 'Ideation', 'Designing', 'Internal Review', 'Stakeholder Review', 'Revisions', 'Finalized', 'Design In Review', 'Design Confirmed'].map((status) => {
        return {
          id: status,
          title: status,
          tasks: this.tasksByStatus[status] || [],
        }
      })
    },
    tasksByStatus() {
      const tasksByStatus = {}
      this.topLevelTasks.forEach((task) => {
        if (!tasksByStatus[task.status]) {
          tasksByStatus[task.status] = []
        }
        tasksByStatus[task.status].push(task)
      })
      return tasksByStatus
    },
    childTasksByParent() {
      return this.filteredTasks.reduce((childrenByParent, task) => {
        if (!task.parent_task) return childrenByParent
        if (!childrenByParent[task.parent_task]) {
          childrenByParent[task.parent_task] = []
        }
        childrenByParent[task.parent_task].push(task)
        return childrenByParent
      }, {})
    },
    topLevelTasks() {
      // ponytail: a subtask whose parent isn't in this list (e.g. My Tasks
      // where only the child is assigned to me) is shown at top level.
      const names = new Set(this.filteredTasks.map((t) => t.name))
      return this.filteredTasks.filter(
        (task) => !task.parent_task || !names.has(task.parent_task),
      )
    },
  },
}
</script>
