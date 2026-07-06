<template>
  <Dialog
    :options="{ size: '6xl' }"
    v-model="showDialog"
    :disableOutsideClickToClose="minimized"
    @after-leave="onAfterLeave"
  >
    <template #body-main>
      <div class="flex items-center justify-between gap-3 border-b border-outline-gray-2 bg-surface-modal px-4 py-3 sm:px-5">
        <h3 class="min-w-0 truncate text-lg font-semibold text-ink-gray-9">{{ dialogTitle }}</h3>
        <div class="flex shrink-0 items-center gap-1">
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
      <div class="max-h-[85vh] min-h-0 overflow-hidden bg-surface-modal">
        <div class="flex h-[80vh] min-h-0 flex-col">
          <TaskDetail
            v-if="activeTaskId"
            :key="activeTaskId"
            :taskId="activeTaskId"
            embedded
            @close="closeDialog"
            @switch-task="activeTaskId = $event"
          />
        </div>
      </div>
    </template>
  </Dialog>
  <div
    v-if="minimized"
    :style="pillStyle"
    class="fixed z-20 flex w-80 items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3 shadow-xl"
  >
    <button
      type="button"
      class="min-w-0 flex-1 truncate text-left text-sm font-medium text-ink-gray-8"
      @click="expand"
    >
      {{ dialogTitle }}
    </button>
    <div class="flex shrink-0 items-center gap-1">
      <button
        type="button"
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Expand"
        @click="expand"
      >
        <LucideMaximize2 class="h-4 w-4" />
      </button>
      <button
        type="button"
        class="rounded p-0.5 text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8"
        aria-label="Close"
        @click="closeFromPill"
      >
        <LucideX class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, getCachedDocumentResource } from 'frappe-ui'
import TaskDetail from '@/components/TaskDetail.vue'
import LucideMinimize2 from '~icons/lucide/minimize-2'
import LucideMaximize2 from '~icons/lucide/maximize-2'
import LucideX from '~icons/lucide/x'
import { nextStackId, pushStack, removeStack, pillStyle as makePillStyle } from '@/utils/minimizedStack'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  taskId: { type: String, default: null },
})

const emit = defineEmits(['update:modelValue', 'closed'])

const showDialog = computed({
  get() {
    return props.modelValue
  },
  set(v) {
    emit('update:modelValue', v)
  },
})

const minimized = ref(false)
const stackId = nextStackId()
const pillStyle = makePillStyle(stackId)
const activeTaskId = ref(null)

watch(
  () => props.taskId,
  (id) => {
    if (id) activeTaskId.value = id
  },
  { immediate: true },
)

watch(
  () => props.modelValue,
  (show) => {
    if (show && props.taskId) {
      activeTaskId.value = props.taskId
      minimized.value = false
      removeStack(stackId)
    }
  },
)

const dialogTitle = computed(() => {
  if (!activeTaskId.value) return 'Task'
  const task = getCachedDocumentResource('GP Task', activeTaskId.value)
  return task?.doc?.title || `Task #${activeTaskId.value}`
})

function minimize() {
  minimized.value = true
  pushStack(stackId)
  showDialog.value = false
}

function expand() {
  minimized.value = false
  removeStack(stackId)
  showDialog.value = true
}

function closeDialog() {
  minimized.value = false
  removeStack(stackId)
  showDialog.value = false
}

function closeFromPill() {
  minimized.value = false
  removeStack(stackId)
  showDialog.value = false
  emit('closed')
}

function onAfterLeave() {
  if (!minimized.value) {
    emit('closed')
  }
}
</script>
