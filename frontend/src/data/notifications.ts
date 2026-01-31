import { createResource } from 'frappe-ui'

export let unreadNotifications = createResource({
  cache: 'Unread Notifications Count',
  url: '/api/v2/method/gameplan.api.unread_notifications',
  auto: true,
  initialData: 0,
})
