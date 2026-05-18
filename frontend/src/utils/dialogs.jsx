import { h, reactive, ref } from 'vue'
import { Dialog, ErrorMessage } from 'frappe-ui'

let dialogs = ref([])

export let Dialogs = {
  name: 'Dialogs',
  render() {
    return dialogs.value.map((dialog) => (
      <Dialog
        options={dialog}
        modelValue={dialog.show}
        onUpdate:modelValue={(val) => (dialog.show = val)}
      >
        {{
          'body-content': () => {
            return [
              dialog.message && (
                <p class="max-w-full whitespace-normal break-words text-p-base text-ink-gray-7">
                  {dialog.message}
                </p>
              ),
              dialog.input && (
                <div class="mt-3">
                  {dialog.input.label && (
                    <label class="mb-1 block text-sm text-ink-gray-5">{dialog.input.label}</label>
                  )}
                  <input
                    class="w-full rounded border border-outline-gray-2 px-3 py-1.5 text-sm text-ink-gray-9 outline-none focus:border-outline-gray-4"
                    type="text"
                    value={dialog.input.value}
                    onInput={(e) => (dialog.input.value = e.target.value)}
                    onKeydown={(e) => {
                      if (e.key === 'Enter' && dialog.input.onEnter) dialog.input.onEnter()
                    }}
                    ref={(el) => el && setTimeout(() => el.focus(), 50)}
                  />
                </div>
              ),
              <ErrorMessage class="mt-2" message={dialog.error} />,
            ]
          },
        }}
      </Dialog>
    ))
  },
}

export function createDialog(dialogOptions) {
  let dialog = reactive(dialogOptions)
  dialog.key = 'dialog-' + dialogs.value.length
  dialog.show = false
  setTimeout(() => {
    dialog.show = true
  }, 0)
  dialogs.value.push(dialog)
}
