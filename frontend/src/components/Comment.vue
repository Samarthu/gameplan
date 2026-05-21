<template>
  <div
    class="py-2.5 transition-shadow"
    :class="{
      'rounded-lg ring-2 ring-blue-200': !comment.loading && highlight,
    }"
    :data-id="comment.name"
  >
    <UserInfo :email="comment.owner" v-slot="{ user }">
      <div
        class="overflow-hidden rounded-lg border border-outline-gray-2 bg-surface-white shadow-sm"
        :class="{ 'border-l-4 border-l-blue-500': !comment.deleted_at }"
      >
        <div class="px-4 pt-4 sm:px-5">
          <div class="flex min-w-0 items-start gap-3.5">
            <UserProfileLink class="shrink-0" :user="user.name">
              <UserAvatar size="md" :user="user.name" />
            </UserProfileLink>
            <div class="min-w-0 flex-1">
              <div class="min-w-0">
                <div class="flex min-w-0 items-center gap-2">
                  <UserProfileLink
                    class="truncate text-base font-semibold leading-5 text-ink-gray-9 hover:text-ink-blue-3"
                    :user="user.name"
                  >
                    {{ user.full_name }}
                  </UserProfileLink>
                  <span v-if="comment.loading" class="shrink-0 text-sm italic text-ink-gray-5">
                    Sending...
                  </span>
                  <span v-if="comment.error" class="shrink-0 text-sm text-ink-red-4">Error</span>
                </div>
                <div
                  class="mt-1 flex flex-wrap items-center gap-x-2 text-sm leading-4 text-ink-gray-5"
                >
                  <time :datetime="comment.creation" :title="$dayjs(comment.creation)">
                    {{ $dayjs(comment.creation).fromNow() }}
                  </time>
                  <span
                    v-if="comment.modified > comment.creation"
                    :title="$dayjs(comment.modified)"
                  >
                    Edited
                  </span>
                </div>
              </div>
            </div>
            <div
              v-show="!comment.editing"
              class="ml-auto flex shrink-0 items-center gap-1 text-ink-gray-5"
            >
              <Tooltip text="Copy link">
                <button
                  type="button"
                  class="rounded-md p-1.5 transition hover:bg-surface-gray-2 hover:text-ink-gray-8"
                  @click="copyLink(comment)"
                >
                  <LucideBookmark class="h-[18px] w-[18px]" />
                </button>
              </Tooltip>
              <Tooltip text="Revisions">
                <button
                  type="button"
                  class="rounded-md p-1.5 transition hover:bg-surface-gray-2 hover:text-ink-gray-8 disabled:cursor-not-allowed disabled:opacity-40"
                  :disabled="comment.modified <= comment.creation"
                  @click="showRevisionsDialog = true"
                >
                  <LucideMessageSquare class="h-[18px] w-[18px]" />
                </button>
              </Tooltip>
              <Tooltip text="Reply">
                <button
                  type="button"
                  class="rounded-md p-1.5 transition hover:bg-surface-gray-2 hover:text-ink-gray-8"
                  @click="$emit('reply', user.full_name)"
                >
                  <LucideReply class="h-[18px] w-[18px]" />
                </button>
              </Tooltip>
              <Dropdown
                placement="right"
                :button="{
                  icon: 'more-horizontal',
                  variant: 'ghost',
                  label: 'Comment Options',
                }"
                :options="[
                  {
                    label: 'Edit',
                    icon: 'edit',
                    onClick: () => (comment.editing = true),
                    condition: () => !comment.deleted_at && !readOnlyMode,
                  },
                  {
                    label: 'Revisions',
                    icon: 'rotate-ccw',
                    onClick: () => (showRevisionsDialog = true),
                    condition: () => comment.modified > comment.creation,
                  },
                  {
                    label: 'Copy link',
                    icon: 'link',
                    onClick: () => copyLink(comment),
                  },
                  {
                    label: 'Delete',
                    icon: 'trash',
                    onClick: () => {
                      $dialog({
                        title: 'Delete comment',
                        message: 'Are you sure you want to delete this comment?',
                        actions: [
                          {
                            label: 'Delete',
                            variant: 'solid',
                            theme: 'red',
                            onClick: (close) => {
                              return comments.setValue
                                .submit({
                                  name: comment.name,
                                  deleted_at: $dayjs().format('YYYY-MM-DD HH:mm:ss'),
                                })
                                .then(close)
                            },
                          },
                        ],
                      })
                    },
                    condition: () =>
                      $isSessionUser(comment.owner) && comment.deleted_at == null && !readOnlyMode,
                  },
                ]"
              />
            </div>
          </div>

          <div class="mt-3 flex gap-3.5">
            <div class="hidden w-8 shrink-0 sm:block"></div>
            <div
              class="min-w-0 flex-1 text-base leading-6 text-ink-gray-8"
              :class="comment.editing && 'rounded-lg border border-outline-gray-2 p-3 focus-within:border-outline-gray-3'"
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
              <span class="text-base italic text-ink-gray-5" v-else> This message is deleted </span>
            </div>
          </div>
        </div>

        <div
          v-if="!comment.deleted_at && !comment.editing"
          class="mt-4 flex min-h-12 items-center justify-between gap-3 border-t border-outline-gray-2 px-4 py-2.5 sm:px-5"
        >
          <Reactions
            v-if="comment.reactions"
            doctype="GP Comment"
            :name="comment.name"
            v-model:reactions="comment.reactions"
            :read-only-mode="readOnlyMode"
          />
          <div v-else></div>
          <button
            type="button"
            class="ml-auto rounded-md px-3 py-1.5 text-sm font-semibold text-ink-gray-6 transition hover:bg-surface-gray-2 hover:text-ink-gray-9"
            @click="$emit('reply', user.full_name)"
          >
            Reply
          </button>
        </div>
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
import { Dropdown, Tooltip } from 'frappe-ui'
import { copyToClipboard } from '@/utils'
import UserProfileLink from './UserProfileLink.vue'
import CommentEditor from './CommentEditor.vue'
import Reactions from './Reactions.vue'
import RevisionsDialog from './RevisionsDialog.vue'
import LucideBookmark from '~icons/lucide/bookmark'
import LucideMessageSquare from '~icons/lucide/message-square'
import LucideReply from '~icons/lucide/reply'

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
  },
  components: {
    UserProfileLink,
    Dropdown,
    Tooltip,
    CommentEditor,
    Reactions,
    RevisionsDialog,
    LucideBookmark,
    LucideMessageSquare,
    LucideReply,
  },
  data() {
    return {
      showRevisionsDialog: false,
    }
  },
  methods: {
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
