const listeners = new Set()

export function onProjectMerged(callback) {
  listeners.add(callback)
  return () => listeners.delete(callback)
}

export function emitProjectMerged(payload = {}) {
  for (const callback of listeners) {
    callback(payload)
  }
}
