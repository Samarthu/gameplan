<template>
  <div>
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-5 py-2.5"
    >
      <Breadcrumbs class="h-7" :items="breadcrumbs">
        <template #prefix="{ item }">
          <span class="mr-2 flex rounded-sm text-2xl leading-none" v-if="item.icon">
            {{ item.icon }}
          </span>
        </template>
      </Breadcrumbs>
      <div class="flex items-center space-x-2">
        <span class="hidden text-sm text-ink-gray-5 sm:block" v-if="page.doc">
          Last updated {{ $dayjs(page.doc.modified).format('LLL') }}
        </span>
        <div
          v-if="page.doc"
          class="flex overflow-hidden rounded-lg border border-outline-gray-modals text-sm"
          role="group"
          aria-label="Page display mode"
        >
          <button
            type="button"
            class="px-3 py-1.5 transition-colors"
            :class="
              !pageEditMode
                ? 'bg-surface-gray-3 font-medium text-ink-gray-9'
                : 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9'
            "
            @click="setPageEditMode(false)"
          >
            View
          </button>
          <button
            type="button"
            class="border-l border-outline-gray-modals px-3 py-1.5 transition-colors"
            :class="
              pageEditMode
                ? 'bg-surface-gray-3 font-medium text-ink-gray-9'
                : 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-9'
            "
            @click="setPageEditMode(true)"
          >
            Edit
          </button>
        </div>
        <button
          v-if="page.doc"
          type="button"
          class="flex h-8 items-center gap-1.5 rounded-md px-2.5 text-sm text-ink-gray-7 transition-colors hover:bg-surface-gray-2"
          :class="{ 'bg-surface-gray-2 text-ink-gray-9': showAttachments }"
          @click="showAttachments = !showAttachments"
          aria-label="Open attachments panel"
          title="Attachments"
        >
          <AttachmentsPaperclip class="h-4 w-4" />
          <span class="hidden sm:inline">Attachments</span>
          <span
            v-if="attachmentCount > 0"
            class="rounded-full bg-surface-gray-3 px-1.5 text-xs font-medium leading-4 text-ink-gray-8"
          >
            {{ attachmentCount }}
          </span>
        </button>
        <Button
          v-show="page.doc && page.isDirty"
          variant="solid"
          @click="save"
          :loading="page.save.loading"
        >
          Save
        </Button>
      </div>
    </header>
    <AttachmentsPanel
      v-if="page.doc"
      v-model="showAttachments"
      :page-id="pageId"
      :editor="$refs.content?.editor"
      @update:count="attachmentCount = $event"
    />
    <div class="mx-auto w-full max-w-4xl px-5">
      <div class="py-6" v-if="page.doc">
        <span class="text-sm text-ink-gray-5 sm:hidden">
          Last updated {{ $dayjs(page.doc.modified).format('LLL') }}
        </span>
        <div class="mb-3 md:px-[70px]">
          <h1
            v-if="!pageEditMode"
            class="break-words pt-4 text-3xl font-semibold leading-tight text-ink-gray-9"
          >
            {{ page.doc.title }}
          </h1>
          <input
            v-else
            class="w-full border-0 bg-surface-white p-0 pt-4 text-3xl font-semibold text-ink-gray-9 focus:outline-none focus:ring-0"
            type="text"
            :value="page.doc.title"
            @input="page.doc.title = $event.target.value"
            @keydown.enter="$refs.content.editor.commands.focus()"
            ref="titleInput"
          />
        </div>
        <TextEditor
          editor-class="rounded-b-lg max-w-[unset] prose-sm pb-[50vh] md:px-[70px]"
          :content="normalizedContent"
          @change="page.doc.content = $event"
          placeholder="Start writing here..."
          :bubbleMenu="pageEditMode"
          :fixedMenu="pageEditMode ? fixedMenuButtons : false"
          :floatingMenu="pageEditMode ? floatingMenuButtons : false"
          :editable="pageEditMode"
          :extensions="editorExtensions"
          ref="content"
        />
      </div>
    </div>
  </div>
</template>
<script>
import { Breadcrumbs, getCachedDocumentResource } from 'frappe-ui'
import TextEditor from '@/components/TextEditor.vue'
import { getTeam } from '@/data/teams'
import { getProject } from '@/data/projects'
import FileAttachment, { FileAttachmentButton } from '@/components/TextEditorFileExtension'
import WebEmbed, { WebEmbedButton } from '@/components/TextEditorEmbedExtension'
import AttachmentsPanel from '@/components/AttachmentsPanel.vue'
import AttachmentsPaperclip from '@/components/TextEditorFileExtension/PaperclipIcon.vue'

// One-time DOM migration for content saved by an earlier version of this
// extension. ProseMirror promotes inline-tag candidates (like <a>) to a
// mark, so the legacy `<a data-file-attachment>` form fails to activate
// the node view on reload — it just renders as a plain hyperlink. We
// rewrite it to `<div data-file-attachment>` (block) before handing the
// HTML to the editor, which makes the node view fire. The next save
// writes the canonical <div> form so the migration only runs once per
// legacy doc.
//
// Safety: input is the GP Page `content` field, already sanitized by
// Frappe (frappe.utils.html_utils.sanitize_html). We use DOMParser to
// build an inert document — scripts inside it are NOT executed.
function migrateLegacyAttachmentTags(html) {
  if (typeof html !== 'string' || !html) return html || ''
  if (!html.includes('data-file-attachment')) return html
  const inert = new DOMParser().parseFromString(html, 'text/html')
  inert.querySelectorAll('a[data-file-attachment]').forEach((a) => {
    const div = inert.createElement('div')
    for (const attr of Array.from(a.attributes)) {
      div.setAttribute(attr.name, attr.value)
    }
    if (!div.hasAttribute('data-src')) {
      const href = a.getAttribute('href') || ''
      if (href) div.setAttribute('data-src', href)
    }
    div.removeAttribute('href')
    div.removeAttribute('target')
    div.removeAttribute('rel')
    const fallback = inert.createElement('a')
    fallback.setAttribute(
      'href',
      a.getAttribute('href') || div.getAttribute('data-src') || '#',
    )
    fallback.setAttribute('target', '_blank')
    fallback.setAttribute('rel', 'noopener noreferrer')
    fallback.textContent =
      a.textContent || a.getAttribute('data-file-name') || 'Attachment'
    div.appendChild(fallback)
    a.replaceWith(div)
  })
  return inert.body ? inert.body.innerHTML : html
}

export default {
  name: 'Page',
  props: ['pageId', 'slug'],
  components: { TextEditor, Breadcrumbs, AttachmentsPanel, AttachmentsPaperclip },
  data() {
    return {
      showAttachments: false,
      attachmentCount: 0,
      pageEditMode: false,
    }
  },
  resources: {
    page() {
      return {
        type: 'document',
        doctype: 'GP Page',
        name: this.pageId,
        onSuccess() {
          this.updateUrlSlug()
          this.$nextTick(() => {
            if (this.pageEditMode) {
              this.$refs.titleInput?.focus()
            }
          })
        },
      }
    },
  },
  mounted() {
    document.addEventListener('keydown', this.handleKeyboardShortcuts)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeyboardShortcuts)
  },
  methods: {
    handleKeyboardShortcuts(e) {
      if (e.key === 's' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        this.save()
      }
    },
    setPageEditMode(on) {
      if (this.pageEditMode === on) return
      this.pageEditMode = on
      this.$nextTick(() => {
        if (on) {
          this.$refs.titleInput?.focus()
          this.$refs.content?.editor?.commands.focus()
        }
      })
    },
    save() {
      this.page.save.submit(null, {
        onSuccess() {
          this.updateUrlSlug()
        },
      })
    },
    updateUrlSlug() {
      if (!this.$route.params.slug || this.$route.params.slug !== this.page.doc.slug) {
        this.$router.replace({
          name: this.page.doc.project ? 'ProjectPage' : 'Page',
          params: {
            ...this.$route.params,
            slug: this.page.doc.slug,
          },
          query: this.$route.query,
        })
      }
    },
  },
  computed: {
    editorExtensions() {
      return [FileAttachment, WebEmbed]
    },
    normalizedContent() {
      return migrateLegacyAttachmentTags(this.page.doc?.content)
    },
    fixedMenuButtons() {
      return [
        'Paragraph',
        ['Heading 1', 'Heading 2', 'Heading 3'],
        'Separator',
        'Bold',
        'Italic',
        'Separator',
        'Bullet List',
        'Numbered List',
        'Separator',
        'Align Left',
        'Align Center',
        'Align Right',
        'FontColor',
        'Separator',
        'Image',
        'Video',
        FileAttachmentButton,
        WebEmbedButton,
        'Link',
        'Separator',
        'Blockquote',
        'Code',
        'Horizontal Rule',
        'Separator',
        [
          'InsertTable',
          'AddColumnBefore',
          'AddColumnAfter',
          'DeleteColumn',
          'AddRowBefore',
          'AddRowAfter',
          'DeleteRow',
          'MergeCells',
          'SplitCell',
          'ToggleHeaderColumn',
          'ToggleHeaderRow',
          'ToggleHeaderCell',
          'DeleteTable',
        ],
        'Separator',
        'Undo',
        'Redo',
      ]
    },
    floatingMenuButtons() {
      return [
        'Paragraph',
        'Heading 2',
        'Heading 3',
        'Bullet List',
        'Numbered List',
        'Blockquote',
        'Code',
        'Horizontal Rule',
        'InsertTable',
      ]
    },
    page() {
      return this.$resources.page
    },
    isDirty() {
      if (!this.page.doc) return false
      return this.page.doc.title !== this.title || this.page.doc.content !== this.content
    },
    breadcrumbs() {
      if (!this.page.doc) return []
      if (!this.page.doc.project) {
        return [
          { label: 'My Documents', route: { name: 'MyPages' } },
          {
            label: this.pageTitle,
            route: {
              name: 'Page',
              params: { pageId: this.pageId, slug: this.slug },
            },
          },
        ]
      }
      let team = getTeam(this.page.doc.team)
      let project = getProject(this.page.doc.project)

      if (!(team && project)) return []
      return [
        {
          label: team.title,
          icon: team.icon,
          route: { name: 'Team', params: { teamId: team.name } },
        },
        {
          label: project.title,
          route: {
            name: 'Project',
            params: {
              teamId: team.name,
              projectId: project.name,
            },
          },
        },
        {
          label: 'Documents',
          route: {
            name: 'ProjectPages',
            params: {
              teamId: team.name,
              projectId: project.name,
            },
          },
        },
        {
          label: this.pageTitle,
          route: {
            name: 'Page',
            params: { pageId: this.pageId, slug: this.slug },
          },
        },
      ]
    },
    pageTitle() {
      let page = getCachedDocumentResource('GP Page', this.pageId)
      return page?.doc?.title || this.pageId
    },
  },
  pageMeta() {
    let project = getProject(this.page.doc?.project)
    return {
      title: project ? `${this.pageTitle} | ${project.title || ''}` : this.pageTitle,
    }
  },
}
</script>
