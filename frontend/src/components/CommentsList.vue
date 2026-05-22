<template>
  <div class="flex flex-col h-full min-h-0">
    <div
      v-if="$resources.comments.data == null"
      class="flex animate-pulse items-start space-x-3 px-2 py-4 text-base"
    >
      <div class="h-8 w-8 rounded-full bg-surface-gray-3"></div>
      <div>
        <div class="flex h-8 flex-col justify-center">
          <div class="h-2 w-40 bg-surface-gray-3"></div>
        </div>
        <div class="flex flex-col gap-2">
          <div v-for="i in 4">
            <div
              class="h-2 bg-surface-gray-3"
              :style="{ width: `${Math.max(Math.random() * 800, 600)}px` }"
            ></div>
          </div>
        </div>
      </div>
    </div>
    <div class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-1 xl:px-6 py-2" ref="scrollContainer">
      <div v-if="showToolbar" class="mb-4 flex items-center justify-between gap-3">
        <Dropdown :options="timelineFilterOptions">
          <button
            class="inline-flex items-center gap-2 rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-base font-semibold text-ink-gray-8 shadow-sm hover:bg-surface-gray-1"
          >
            {{ timelineFilterLabel }}
            <LucideChevronDown class="h-4 w-4 text-ink-gray-6" />
          </button>
        </Dropdown>
        <Dropdown :options="timelineSortOptions">
          <button
            class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-base font-semibold text-ink-gray-8 hover:bg-surface-gray-1"
          >
            {{ timelineSortLabel }}
            <LucideChevronDown class="h-4 w-4 text-ink-gray-6" />
          </button>
        </Dropdown>
      </div>

      <div class="relative">
        <div
          v-if="timelineItems.length"
          class="absolute bottom-0 left-[1.375rem] top-0 w-px bg-outline-gray-2"
          aria-hidden="true"
        ></div>
      <template v-for="(item, index) in timelineItems" :key="item.doctype + item.name">
        <div
          v-if="newMessagesFrom && newMessagesFrom == item.name"
          class="relative my-4"
          role="separator"
        >
          <div class="border-b border-blue-600"></div>
          <span
            class="absolute -top-2 left-1/2 -translate-x-1/2 bg-surface-white px-2 text-sm font-medium text-ink-blue-3"
          >
            New comments
          </span>
        </div>
        <Comment
          v-if="item.doctype == 'GP Comment'"
          class="relative mb-4 ml-8"
          :ref="($comment) => setItemRef($comment, item)"
          :comment="item"
          :highlight="highlightedItem == item"
          :readOnlyMode="readOnlyMode"
          :comments="$resources.comments"
          :number="timelineNumber(index)"
          @reply="replyToComment"
        />
        <template v-else-if="item.doctype == 'GP Activity'">
          <Activity
            class="relative mb-4"
            :activity="item"
            :number="timelineNumber(index)"
          />
        </template>
        <Poll
          class="relative mb-4 ml-8 rounded-lg border border-outline-gray-2 bg-surface-white"
          v-else-if="item.doctype == 'GP Poll'"
          :ref="($poll) => setItemRef($poll, item)"
          :highlight="highlightedItem == item"
          :poll="item"
          :readOnlyMode="readOnlyMode"
        />
      </template>
      </div>
    </div>

    <div v-if="!readOnlyMode && !disableNewComment" class="px-1 xl:px-6 py-4 xl:border-t xl:border-outline-gray-2 bg-surface-white z-[1]" ref="addComment">
      <div class="flex items-start min-w-0">
        <div class="mr-3 hidden h-8 items-center sm:flex">
          <UserAvatar :user="$user().name" size="md" />
        </div>
        <div class="relative w-full" v-show="!showCommentBox">
          <button
            class="flex w-full items-center rounded-md border px-2 py-2 text-left text-base text-ink-gray-5 hover:border-outline-gray-3"
            @click="showCommentBox = true"
            @focus="showCommentBox = true"
          >
            Add a comment
          </button>
          <div class="absolute inset-y-0 right-0 flex items-center pr-1">
            <Tooltip text="Add a poll">
              <Button
                variant="ghost"
                label="Add a poll"
                @click="
                  () => {
                    newCommentType = 'Poll'
                    showCommentBox = true
                  }
                "
              >
                <template #icon>
                  <LucideBarChart2 class="w-4 -rotate-90" />
                </template>
              </Button>
            </Tooltip>
          </div>
        </div>
        <div
          v-show="showCommentBox"
          class="w-full min-w-0 rounded-lg border bg-surface-white p-4 focus-within:border-outline-gray-3"
          @keydown.ctrl.enter.capture.stop="submitComment"
          @keydown.meta.enter.capture.stop="submitComment"
        >
          <div class="mb-4 flex items-center sm:hidden">
            <UserAvatar :user="$user().name" size="sm" />
            <span class="ml-2 text-base font-medium text-ink-gray-9">
              {{ $user().full_name }}
            </span>
          </div>
          <CommentEditor
            ref="newCommentEditor"
            v-show="newCommentType == 'Comment'"
            :value="newComment"
            @change="onNewCommentChange"
            :submitButtonProps="{
              variant: 'solid',
              onClick: submitComment,
              loading: $resources.comments.insert.loading,
              disabled: commentEmpty,
            }"
            :discardButtonProps="{
              onClick: discardComment,
            }"
            :editable="showCommentBox"
            placeholder="Add a comment"
          />
          <PollEditor
            v-show="newCommentType == 'Poll'"
            v-model:poll="newPoll"
            :submitButtonProps="{
              onClick: submitPoll,
              loading: $resources.polls.insert.loading,
            }"
            :discardButtonProps="{
              onClick: discardPoll,
            }"
          />
          <ErrorMessage :message="$resources.polls.insert.error" />
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { nextTick } from 'vue'
import { Dropdown, TabButtons } from 'frappe-ui'
import CommentEditor from '@/components/CommentEditor.vue'
import Comment from './Comment.vue'
import Activity from './Activity.vue'
import PollEditor from './PollEditor.vue'
import Poll from './Poll.vue'
import { getScrollContainer } from '@/utils/scrollContainer'
import { Tooltip } from 'frappe-ui'

export default {
  name: 'CommentsArea',
  props: {
    doctype: String,
    name: String,
    newCommentsFrom: String,
    readOnlyMode: Boolean,
    disableNewComment: Boolean,
    filter: String,
    sort: {
      type: String,
      default: 'desc',
    },
    showToolbar: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['update:filter', 'update:sort'],
  components: {
    CommentEditor,
    Comment,
    Activity,
    TabButtons,
    Dropdown,
    PollEditor,
    Poll,
    Tooltip,
  },
  data() {
    let draftComment = localStorage.getItem(this.draftCommentKey())
    return {
      commentMap: {},
      showCommentBox: false,
      newCommentType: 'Comment',
      newComment: draftComment || '',
      newPoll: {
        title: '',
        multiple_answers: false,
        options: [
          { title: '', idx: 1 },
          { title: '', idx: 2 },
        ],
      },
      newMessagesFrom: this.newCommentsFrom,
      highlightedItem: null,
      timelineFilter: this.filter || 'all',
      timelineSort: this.sort || 'desc',
    }
  },
  watch: {
    filter(val) {
      this.timelineFilter = val || 'all'
    },
    sort(val) {
      this.timelineSort = val || 'desc'
    },
    showCommentBox(val) {
      if (val) {
        nextTick(() => {
          this.$refs.newCommentEditor?.editor.commands.focus()
          this.scrollToEnd()
        })
      }
    },
  },
  mounted() {
    if (!this.$refs.newCommentEditor?.editor.isEmpty) {
      this.showCommentBox = true
    }
    this.$socket.on('new_activity', (data) => {
      if (data.reference_doctype == this.doctype && data.reference_name == this.name) {
        this.$resources.activities.reload()
      }
    })
  },
  beforeUnmount() {
    this.$socket.off('new_activity')
  },
  resources: {
    comments() {
      return {
        type: 'list',
        doctype: 'GP Comment',
        cache: ['Comments', this.doctype, this.name],
        fields: [
          'name',
          'content',
          'owner',
          'creation',
          'modified',
          'deleted_at',
          { reactions: ['name', 'user', 'emoji'] },
        ],
        transform(data) {
          for (let d of data) {
            d.doctype = 'GP Comment'
          }
          return data
        },
        filters: {
          reference_doctype: this.doctype,
          reference_name: this.name,
        },
        orderBy: 'creation asc',
        pageLength: 99999,
        auto: true,
        onSuccess() {
          if (this.$route.query.comment) {
            let comment = this.$resources.comments.getRow(this.$route.query.comment)
            this.scrollToItem(comment)
          } else if (!this.$route.query.fromSearch && this.$resources.comments.data.length > 0) {
            this.scrollToEnd()
          }
        },
      }
    },
    activities() {
      return {
        type: 'list',
        doctype: 'GP Activity',
        fields: ['name', 'user', 'action', 'data', 'creation'],
        filters: {
          reference_doctype: this.doctype,
          reference_name: this.name,
        },
        orderBy: 'creation asc',
        pageLength: 99999,
        auto: true,
        transform(activities) {
          for (let activity of activities) {
            activity.doctype = 'GP Activity'
            activity.data = activity.data ? JSON.parse(activity.data) : null
          }
          return activities
        },
      }
    },
    polls() {
      return {
        type: 'list',
        doctype: 'GP Poll',
        fields: [
          'name',
          'title',
          'anonymous',
          'multiple_answers',
          'creation',
          'owner',
          'stopped_at',
          { options: ['name', 'title', 'idx', 'percentage'] },
          { votes: ['user', 'title'] },
          { reactions: ['name', 'user', 'emoji'] },
        ],
        filters: {
          discussion: this.name,
        },
        orderBy: 'creation asc',
        auto: true,
        pageLength: 99999,
        transform(data) {
          for (let d of data) {
            d.doctype = 'GP Poll'
          }
          return data
        },
        onSuccess() {
          if (this.$route.query.poll) {
            let poll = this.$resources.polls.getRow(this.$route.query.poll)
            this.scrollToItem(poll)
          }
        },
      }
    },
  },
  methods: {
    submitComment() {
      if (this.commentEmpty) {
        return
      }
      this.$resources.comments.setData((data) => {
        data.push({
          owner: this.$user().name,
          content: this.newComment,
          reference_doctype: this.doctype,
          reference_name: this.name,
          loading: true,
          reactions: [],
          creation: this.$dayjs().format('YYYY-MM-DD HH:mm:ss'),
        })
        return data
      })
      this.$resources.comments.insert.submit(
        {
          reference_doctype: this.doctype,
          reference_name: this.name,
          content: this.newComment,
        },
        {
          onError(error) {
            this.$resources.comments.setData((data) => {
              let lastComment = data[data.length - 1]
              lastComment.loading = false
              lastComment.error = error
              return data
            })
            this.$toast({
              title: 'Error adding new comment',
              text: error.messages.join(', '),
              position: 'bottom-center',
              icon: 'alert-circle',
              iconClasses: 'text-ink-red-4',
            })
          },
        },
      )
      this.resetCommentState()
    },
    async scrollToItem(item) {
      if (!item) return
      await nextTick()
      if (item.$el) {
        this.highlightedItem = item
        this.scrollToElement(item.$el)
      }
      setTimeout(() => {
        this.highlightedItem = null
        this.$router.replace({ query: {} })
      }, 10000)
    },
    getScrollContainer() {
      let container = this.$refs.scrollContainer
      if (container && window.innerWidth >= 1280) {
        return container
      }
      return getScrollContainer()
    },
    scrollToElement($el) {
      let scrollContainer = this.getScrollContainer()
      if (scrollContainer === this.$refs.scrollContainer) {
        let containerRect = scrollContainer.getBoundingClientRect()
        let elRect = $el.getBoundingClientRect()
        let top = elRect.top - containerRect.top
        scrollContainer.scrollBy({ top, left: 0, behavior: 'smooth' })
      } else {
        let headerHeight = 64
        let top = $el.offsetTop - scrollContainer.scrollTop - headerHeight
        scrollContainer.scrollBy({ top, left: 0, behavior: 'smooth' })
      }
    },
    scrollToEnd() {
      let scrollContainer = this.getScrollContainer()
      scrollContainer.scrollTop = scrollContainer.scrollHeight
    },
    discardComment() {
      if (!this.editorObject.isEmpty) {
        this.$dialog({
          title: 'Discard comment',
          message: 'Are you sure you want to discard your comment?',
          actions: [
            {
              label: 'Discard comment',
              onClick: (close) => {
                this.resetCommentState()
                close()
              },
              variant: 'solid',
            },
            {
              label: 'Keep comment',
            },
          ],
        })
      } else {
        this.resetCommentState()
      }
    },
    onNewCommentChange(content) {
      this.newComment = content

      // save draft comment to local storage
      setTimeout(() => {
        // set timeout to move it off main thread
        localStorage.setItem(this.draftCommentKey(), content)
      }, 0)
    },
    replyToComment(fullName) {
      let mention = fullName ? `@${fullName} ` : ''
      if (!this.showCommentBox) {
        this.showCommentBox = true
      }
      if (!this.newComment || this.newComment === '<p></p>') {
        this.newComment = `<p>${mention}</p>`
      }
      nextTick(() => {
        this.$refs.newCommentEditor?.editor.commands.focus('end')
      })
    },
    resetCommentState() {
      localStorage.removeItem(this.draftCommentKey())
      this.$resetData([
        'newComment',
        'showCommentBox',
        'newCommentType',
        'newPoll',
        'highlightedItem',
      ])
    },
    submitPoll() {
      if (this.doctype !== 'GP Discussion') return
      return this.$resources.polls.insert.submit(
        {
          ...this.newPoll,
          discussion: this.name,
        },
        {
          onSuccess() {
            this.resetCommentState()
          },
        },
      )
    },
    discardPoll() {
      this.resetCommentState()
    },
    draftCommentKey() {
      return `draft-comment-${this.doctype}-${this.name}`
    },
    setItemRef($component, item) {
      if ($component?.$el) {
        item.$el = $component.$el
      }
    },
    setTimelineFilter(filter) {
      this.timelineFilter = filter
      this.$emit('update:filter', filter)
    },
    setTimelineSort(sort) {
      this.timelineSort = sort
      this.$emit('update:sort', sort)
    },
    timelineNumber(index) {
      if (this.timelineSort === 'desc') {
        return this.timelineItems.length - index
      }
      return index + 1
    },
  },
  computed: {
    timelineFilterOptions() {
      return [
        { label: 'Show everything', onClick: () => this.setTimelineFilter('all') },
        { label: 'Show comments', onClick: () => this.setTimelineFilter('comments') },
        { label: 'Show activity', onClick: () => this.setTimelineFilter('activity') },
      ]
    },
    timelineFilterLabel() {
      return {
        all: 'Show everything',
        comments: 'Show comments',
        activity: 'Show activity',
      }[this.timelineFilter] || 'Show everything'
    },
    timelineSortOptions() {
      return [
        { label: 'Newest on top', onClick: () => this.setTimelineSort('desc') },
        { label: 'Oldest on top', onClick: () => this.setTimelineSort('asc') },
      ]
    },
    timelineSortLabel() {
      return this.timelineSort === 'desc' ? 'Newest on top' : 'Oldest on top'
    },
    timelineItems() {
      let items = []
      const f = this.timelineFilter || 'all'
      if (f === 'all' || f === 'comments') {
        if (this.$resources.comments.data?.length) {
          items = items.concat(this.$resources.comments.data)
        }
        if (this.$resources.polls.data?.length) {
          items = items.concat(this.$resources.polls.data)
        }
      }
      if (f === 'all' || f === 'activity') {
        if (this.$resources.activities.data?.length) {
          items = items.concat(this.$resources.activities.data)
        }
      }
      return items.sort((a, b) => {
        const diff = new Date(a.creation) - new Date(b.creation)
        return this.timelineSort === 'desc' ? -diff : diff
      })
    },
    commentEmpty() {
      return !this.newComment || this.newComment === '<p></p>'
    },
    editorObject() {
      return this.$refs.newCommentEditor?.editor
    },
  },
}
</script>
