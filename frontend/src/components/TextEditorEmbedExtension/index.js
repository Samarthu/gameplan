import { Node, mergeAttributes } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import { defineAsyncComponent } from 'vue'
import Component from './Component.vue'
import { resolveEmbed, isAllowedEmbedSrc } from './providers'

export const WebEmbed = Node.create({
  name: 'web-embed',
  group: 'block',
  atom: true,
  draggable: true,
  selectable: true,

  addAttributes() {
    return {
      src: {
        default: '',
        parseHTML: (el) => {
          const src = el.getAttribute('data-src') || el.getAttribute('src') || ''
          return isAllowedEmbedSrc(src) ? src : ''
        },
        renderHTML: (attrs) => ({ 'data-src': attrs.src || '' }),
      },
      provider: {
        default: '',
        parseHTML: (el) => el.getAttribute('data-provider') || '',
        renderHTML: (attrs) => ({ 'data-provider': attrs.provider || '' }),
      },
      aspectRatio: {
        default: '16 / 9',
        parseHTML: (el) => el.getAttribute('data-aspect') || '16 / 9',
        renderHTML: (attrs) => ({
          'data-aspect': attrs.aspectRatio || '16 / 9',
        }),
      },
    }
  },

  // New storage form: `<div data-web-embed data-src data-provider data-aspect>`
  // so Frappe's HTML sanitizer doesn't strip the tag. Keeps backward compat
  // with the old `<web-embed>` tag for any pre-existing saved content.
  parseHTML() {
    return [
      { tag: 'div[data-web-embed]', priority: 1000 },
      { tag: 'web-embed', priority: 1000 },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'div',
      mergeAttributes({ 'data-web-embed': '' }, HTMLAttributes),
    ]
  },

  addNodeView() {
    return VueNodeViewRenderer(Component)
  },

  addCommands() {
    return {
      insertWebEmbed:
        (url) =>
        ({ chain }) => {
          const resolved = resolveEmbed(url)
          if (!resolved) return false
          return chain()
            .focus()
            .insertContent({
              type: this.name,
              attrs: resolved,
            })
            .run()
        },
    }
  },
})

export const WebEmbedButton = {
  label: 'Embed (YouTube, Vimeo, Loom, Figma, Drive)',
  icon: defineAsyncComponent(() => import('./EmbedIcon.vue')),
  isActive: () => false,
  component: defineAsyncComponent(() => import('./InsertEmbed.vue')),
}

export default WebEmbed
