<template>
  <div
    class="relative overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white shadow-sm transition-shadow"
    :class="{
      'ring-2 ring-blue-200': !comment.loading && highlight,
    }"
    :data-id="comment.name"
  >
    <UserInfo :email="comment.owner" v-slot="{ user }">
      <div class="flex items-center gap-2 border-b border-outline-gray-1 bg-surface-gray-1 px-3 py-2">
        <UserProfileLink :user="user.name" class="shrink-0">
          <UserAvatar size="sm" :user="user.name" />
        </UserProfileLink>
        <UserProfileLink
          class="text-base font-semibold leading-5 text-ink-gray-9 hover:text-ink-blue-3"
          :user="user.name"
        >
          {{ user.full_name }}
        </UserProfileLink>
        <time
          class="text-sm text-ink-gray-5"
          :datetime="comment.creation"
          :title="$dayjs(comment.creation)"
        >
          {{ $dayjs(comment.creation).format('DD/MM/YYYY hh:mm A') }}
        </time>
        <span v-if="comment.modified > comment.creation" class="text-xs text-ink-gray-5">
          (edited)
        </span>
        <span v-if="comment.loading" class="text-sm italic text-ink-gray-5">Sending...</span>
        <span v-if="comment.error" class="text-sm text-ink-red-4">Error</span>
        <div class="ml-auto flex items-center gap-2 text-ink-gray-5">
          <span v-if="number" class="text-sm">#{{ number }}</span>
          <Dropdown
            v-show="!comment.editing"
            placement="right"
            :button="{
              icon: 'more-horizontal',
              variant: 'ghost',
              label: 'Comment Options',
            }"
            :options="menuOptions(user)"
          />
        </div>
      </div>

      <div
        class="px-3 py-3 text-base leading-6 text-ink-gray-8"
        :class="comment.editing && 'rounded-md border border-outline-gray-2 m-2 focus-within:border-outline-gray-3'"
        @keydown.ctrl.enter.capture.stop="editComment(comment)"
        @keydown.meta.enter.capture.stop="editComment(comment)"
      >
        <CommentEditor
          v-if="comment.deleted_at == null"
          :value="comment.content"
          @change="comment.content = $event"
          :editable="comment.editing || false"
          :submitButtonProps="{
            onClick: () => editComment(comment),
            loading: comment.loading,
          }"
          :discardButtonProps="{
            onClick: () => {
              comment.editing = false
              comments.fetchOne.submit(comment.name)
            },
          }"
        />
        <span class="italic text-ink-gray-5" v-else>This message is deleted</span>
      </div>

      <div
        v-if="!comment.deleted_at && !comment.editing"
        class="px-3 pb-3"
      >
        <Reactions
          v-if="comment.reactions"
          doctype="GP Comment"
          :name="comment.name"
          v-model:reactions="comment.reactions"
          :read-only-mode="readOnlyMode"
        />
      </div>
    </UserInfo>
    <RevisionsDialog
      v-model="showRevisionsDialog"
      doctype="GP Comment"
      :name="comment.name"
      fieldname="content"
    />
  </div>
</template>
<script>
import { Dropdown } from 'frappe-ui'
import { copyToClipboard } from '@/utils'
import UserProfileLink from './UserProfileLink.vue'
import CommentEditor from './CommentEditor.vue'
import Reactions from './Reactions.vue'
import RevisionsDialog from './RevisionsDialog.vue'

export default {
  name: 'Comment',
  emits: ['reply'],
  props: {
    comment: {
      type: Object,
      required: true,
    },
    readOnlyMode: {
      type: Boolean,
      default: false,
    },
    highlight: {
      type: Boolean,
      default: false,
    },
    comments: {
      type: Object,
    },
    number: {
      type: Number,
      default: null,
    },
  },
  components: {
    UserProfileLink,
    Dropdown,
    CommentEditor,
    Reactions,
    RevisionsDialog,
  },
  data() {
    return {
      showRevisionsDialog: false,
    }
  },
  methods: {
    menuOptions(user) {
      return [
        {
          label: 'Reply',
          icon: 'corner-up-left',
          onClick: () => this.$emit('reply', user.full_name),
          condition: () => !this.readOnlyMode,
        },
        {
          label: 'Edit',
          icon: 'edit',
          onClick: () => (this.comment.editing = true),
          condition: () => !this.comment.deleted_at && !this.readOnlyMode && this.$isSessionUser(this.comment.owner),
        },
        {
          label: 'Revisions',
          icon: 'rotate-ccw',
          onClick: () => (this.showRevisionsDialog = true),
          condition: () => this.comment.modified > this.comment.creation,
        },
        {
          label: 'Copy link',
          icon: 'link',
          onClick: () => this.copyLink(this.comment),
        },
        {
          label: 'Delete',
          icon: 'trash',
          onClick: () => this.confirmDelete(),
          condition: () =>
            this.$isSessionUser(this.comment.owner) &&
            this.comment.deleted_at == null &&
            !this.readOnlyMode,
        },
      ]
    },
    confirmDelete() {
      this.$dialog({
        title: 'Delete comment',
        message: 'Are you sure you want to delete this comment?',
        actions: [
          {
            label: 'Delete',
            variant: 'solid',
            theme: 'red',
            onClick: (close) => {
              return this.comments.setValue
                .submit({
                  name: this.comment.name,
                  deleted_at: this.$dayjs().format('YYYY-MM-DD HH:mm:ss'),
                })
                .then(close)
            },
          },
        ],
      })
    },
    editComment(comment) {
      comment.loading = true
      comment.editing = false
      this.comments.setValue.submit(
        {
          name: comment.name,
          content: comment.content,
        },
        {
          onSuccess() {
            comment.loading = false
          },
          onError(error) {
            comment.loading = false
            comment.error = error
          },
        },
      )
    },
    copyLink(comment) {
      let location = window.location
      let url = `${location.origin}${location.pathname}?comment=${comment.name}`
      copyToClipboard(url)
    },
  },
}
</script>
