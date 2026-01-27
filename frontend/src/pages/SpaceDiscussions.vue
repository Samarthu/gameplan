<template>
  <div class="body-container mt-5">
    <div class="flex mb-4 items-center justify-between">
      <SpaceTabs :spaceId="spaceId" />
      <Button variant="solid" :route="{ name: 'NewDiscussion', query: { spaceId: spaceId } }">
        <template #prefix><LucidePlus class="h-4 w-4" /></template>
        Add new
      </Button>
    </div>
    <DiscussionList
      class="-mx-3"
      :filters="() => ({ project: spaceId })"
      :cacheKey="`SpaceDiscussions-${spaceId}`"
    />
  </div>
</template>
<script setup lang="ts">
import DiscussionList from '@/components/DiscussionList.vue'
import SpaceTabs from '@/components/SpaceTabs.vue'

defineProps<{
  spaceId: string
}>()
</script>
