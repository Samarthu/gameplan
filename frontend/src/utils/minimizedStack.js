import { ref, computed } from 'vue'

// Tracks which dialogs are currently minimized so their floating pills
// stack vertically at the bottom-right instead of overlapping.
const stack = ref([])
let counter = 0

export function nextStackId() {
  return `pill-${++counter}`
}

export function pushStack(id) {
  if (!stack.value.includes(id)) stack.value = [...stack.value, id]
}

export function removeStack(id) {
  stack.value = stack.value.filter((x) => x !== id)
}

// Reactive style for a pill: anchors bottom-right and offsets upward
// based on its position in the minimized stack.
export function pillStyle(id) {
  return computed(() => {
    const index = stack.value.indexOf(id)
    const offset = index < 0 ? 0 : index
    return {
      right: '1rem',
      bottom: `${1 + offset * 4.5}rem`,
    }
  })
}
