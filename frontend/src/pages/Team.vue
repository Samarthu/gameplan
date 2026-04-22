<template>
  <div class="pb-20">
    <header class="sticky top-0 z-10 border-b bg-surface-white px-5 py-2.5">
      <div class="flex items-center justify-between">
        <Breadcrumbs
          class="h-7"
          :items="[
            {
              label: team.doc.title,
              route: { name: 'Team', params: { teamId: team.doc.name } },
            },
          ]"
        >
          <template #prefix>
            <IconPicker
              v-model="team.doc.icon"
              @update:modelValue="team.setValueDebounced.submit({ icon: team.doc.icon })"
              v-slot="{ isOpen }"
            >
              <button
                class="mr-2 flex rounded-sm text-2xl leading-none"
                :class="isOpen ? 'bg-surface-gray-3' : 'hover:bg-surface-gray-2'"
              >
                {{ team.doc.icon }}
              </button>
            </IconPicker>
          </template>
        </Breadcrumbs>

        <div class="flex items-center space-x-2">
          <TeamMembers :team="team" />
          <Dropdown
            v-if="!team.doc.archived_at"
            placement="left"
            :options="[
              {
                label: 'Set cover image',
                icon: 'image',
                condition: () => !team.doc.cover_image,
                onClick: () => (showCoverImage = true),
              },
              {
                label: team.doc.is_private ? 'Make public' : 'Make private',
                icon: team.doc.is_private ? 'globe' : 'lock',
                onClick: () => toggleVisibility(),
              },
              {
                label: 'Archive',
                icon: 'trash-2',
                onClick: () => archiveTeam(),
              },
            ]"
            :button="{
              label: 'Options',
              variant: 'ghost',
              icon: 'more-horizontal',
            }"
          />
        </div>
      </div>
    </header>
    <CoverImage
      v-if="showCoverImage"
      :imageUrl="team.doc.cover_image"
      :imagePosition="team.doc.cover_image_position"
      :editable="true"
      @change="
        ({ imageUrl, imagePosition }) => {
          team.setValue.submit({
            cover_image: imageUrl,
            cover_image_position: imagePosition,
          })
        }
      "
    />
    <router-view class="mx-auto max-w-4xl px-5" :team="team" />
  </div>
</template>
<script>
import { Breadcrumbs, Dropdown, Badge, Tooltip } from 'frappe-ui'
import IconPicker from '@/components/IconPicker.vue'
import Tabs from '@/components/Tabs.vue'
import { teams } from '@/data/teams'

export default {
  name: 'Team',
  props: ['team'],
  components: {
    Breadcrumbs,
    Dropdown,
    IconPicker,
    Tabs,
    Tooltip,
    Badge,
  },
  data() {
    return {
      showCoverImage: Boolean(this.team.doc.cover_image),
    }
  },
  methods: {
    updateTeamIcon(icon) {
      this.team.setValue.submit({ icon })
    },
    archiveTeam() {
      this.$dialog({
        title: 'Archive Team',
        message: 'Are you sure you want to archive the team?',
        actions: [
          {
            label: 'Archive',
            variant: 'solid',
            onClick: (close) => {
              return this.team.archive.submit(null, {
                onSuccess: () => {
                  this.$router.replace({ name: 'Home' })
                  close()
                },
              })
            },
          },
        ],
      })
    },
    toggleVisibility() {
      const makingPrivate = !this.team.doc.is_private
      this.$dialog({
        title: makingPrivate ? 'Make team private' : 'Make team public',
        message: makingPrivate
          ? 'Only team members will be able to see this team and its projects. Continue?'
          : 'Everyone in the workspace will be able to see this team. Continue?',
        actions: [
          {
            label: makingPrivate ? 'Make private' : 'Make public',
            variant: 'solid',
            onClick: (close) => {
              return this.team.setValue.submit(
                { is_private: makingPrivate ? 1 : 0 },
                {
                  onSuccess: () => {
                    if (teams.reload) teams.reload()
                    close()
                  },
                },
              )
            },
          },
        ],
      })
    },
  },
}
</script>
