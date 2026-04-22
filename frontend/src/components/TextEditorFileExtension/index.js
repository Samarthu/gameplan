import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import { defineAsyncComponent } from 'vue'
import Component from './Component.vue'

function toSafeString(v) {
  if (v === null || v === undefined) return ''
  if (typeof v === 'string') return v
  if (typeof v === 'number') return String(v)
  return ''
}

function toSafeInt(v) {
  const n = Number(v)
  return Number.isFinite(n) ? Math.trunc(n) : 0
}

export const FileAttachment = Node.create({
  name: 'file-attachment',
  group: 'block',
  atom: true,
  draggable: true,
  selectable: true,

  addAttributes() {
    return {
      src: {
        default: '',
        parseHTML: (el) => {
          // Prefer data-src (new <div> form), fall back to an inner <a href>
          // (fallback link), then the element's own href (legacy <a> form).
          const dataSrc = el.getAttribute('data-src')
          if (dataSrc) return toSafeString(dataSrc)
          const innerA = el.querySelector && el.querySelector('a[href]')
          if (innerA) return toSafeString(innerA.getAttribute('href'))
          return toSafeString(el.getAttribute('href') || el.getAttribute('src'))
        },
        renderHTML: (attrs) => ({ 'data-src': toSafeString(attrs.src) }),
      },
      fileName: {
        default: '',
        parseHTML: (el) => toSafeString(el.getAttribute('data-file-name')),
        renderHTML: (attrs) => ({
          'data-file-name': toSafeString(attrs.fileName),
        }),
      },
      fileSize: {
        default: 0,
        parseHTML: (el) => toSafeInt(el.getAttribute('data-file-size')),
        renderHTML: (attrs) => ({
          'data-file-size': String(toSafeInt(attrs.fileSize)),
        }),
      },
      mimeType: {
        default: '',
        parseHTML: (el) => toSafeString(el.getAttribute('data-mime-type')),
        renderHTML: (attrs) => ({
          'data-mime-type': toSafeString(attrs.mimeType),
        }),
      },
    }
  },

  // Use a block-level tag (`<div>`) in the storage form. `<a>` is an
  // inline tag; ProseMirror promotes inline-tag candidates to a mark
  // (@tiptap/extension-link wins) even when a higher-priority node rule
  // matches. A `<div data-file-attachment>` is unambiguously block-level,
  // so the node rule wins cleanly. Legacy `<a data-file-attachment>` and
  // `<file-attachment>` are still parsed (DOM migration in Page.vue
  // rewrites legacy <a> to <div> on first load so they render correctly
  // and self-heal on the next save).
  parseHTML() {
    return [
      { tag: 'div[data-file-attachment]', priority: 1000 },
      { tag: 'a[data-file-attachment]', priority: 1000 },
      { tag: 'file-attachment', priority: 1000 },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    const label = toSafeString(node.attrs.fileName) || 'Attachment'
    const src = toSafeString(node.attrs.src)
    return [
      'div',
      mergeAttributes({ 'data-file-attachment': '' }, HTMLAttributes),
      // Nested <a> is the plain-HTML fallback: if JS / node view fail,
      // users still see a clickable link with the filename.
      [
        'a',
        { href: src, target: '_blank', rel: 'noopener noreferrer' },
        label,
      ],
    ]
  },

  addNodeView() {
    return VueNodeViewRenderer(Component)
  },

  addCommands() {
    return {
      insertFileAttachment:
        (attrs) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: {
              src: toSafeString(attrs && attrs.src),
              fileName: toSafeString(attrs && attrs.fileName),
              fileSize: toSafeInt(attrs && attrs.fileSize),
              mimeType: toSafeString(attrs && attrs.mimeType),
            },
          })
        },
    }
  },
})

export const FileAttachmentButton = {
  label: 'Attach File',
  icon: defineAsyncComponent(() => import('./PaperclipIcon.vue')),
  isActive: () => false,
  component: defineAsyncComponent(() => import('./InsertFile.vue')),
}

export default FileAttachment
