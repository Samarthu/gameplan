const EXPORT_COLUMNS = [
  { key: 'name', label: 'ID', required: true },
  { key: 'title', label: 'Task', required: true },
  { key: 'task_type', label: 'Type', columnKey: 'task_type', defaultSelected: true },
  { key: 'status', label: 'Status', columnKey: 'status' },
  { key: 'priority', label: 'Priority', columnKey: 'priority' },
  { key: 'due_date', label: 'Due Date', columnKey: 'due_date' },
  { key: 'assignee', label: 'Assignee', columnKey: 'assignee' },
  { key: 'tags', label: 'Tags', columnKey: 'tags' },
  { key: 'project', label: 'Project', columnKey: 'project' },
  { key: 'team', label: 'Team', columnKey: 'team' },
  { key: 'modified', label: 'Modified', columnKey: 'modified' },
  { key: 'created_by', label: 'Created By', columnKey: 'created_by' },
  { key: 'description', label: 'Description' },
  { key: 'start_date', label: 'Start Date' },
  { key: 'sprint', label: 'Sprint' },
  { key: 'comments_count', label: 'Comments' },
]

export function getExportColumnDefs() {
  return EXPORT_COLUMNS
}

export function getDefaultExportSelection(columnsVisibility = {}) {
  const selection = {}
  for (const col of EXPORT_COLUMNS) {
    if (col.required) {
      selection[col.key] = true
      continue
    }
    if (col.columnKey && columnsVisibility[col.columnKey]) {
      selection[col.key] = true
      continue
    }
    if (col.defaultSelected) {
      selection[col.key] = true
    }
  }
  return selection
}

function escapeCsv(value) {
  const text = value == null ? '' : String(value)
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

function parseTags(task) {
  const raw = task._user_tags || task.tags
  if (!raw) return ''
  if (Array.isArray(raw)) return raw.join(', ')
  return String(raw)
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
    .join(', ')
}

function assigneeLabel(task, getUser) {
  const ids = []
  const seen = new Set()
  const add = (id) => {
    if (!id || seen.has(id)) return
    seen.add(id)
    ids.push(id)
  }

  if (Array.isArray(task.assignees)) {
    for (const row of task.assignees) {
      add(typeof row === 'object' && row ? row.user : null)
    }
  }

  const rawAssignees = task.assignee_users
  if (Array.isArray(rawAssignees)) {
    rawAssignees.forEach(add)
  } else if (typeof rawAssignees === 'string' && rawAssignees.trim()) {
    try {
      const parsed = JSON.parse(rawAssignees)
      if (Array.isArray(parsed)) parsed.forEach(add)
      else add(rawAssignees)
    } catch {
      add(rawAssignees)
    }
  }

  add(task.assigned_to)

  return ids.map((id) => getUser(id)?.full_name || id).join(', ')
}

function formatTaskValue(task, key, { getUser, dayjs }) {
  switch (key) {
    case 'name':
      return task.name
    case 'title':
      return task.title
    case 'task_type':
      return task.task_type || ''
    case 'status':
      return task.status || ''
    case 'priority':
      return task.priority || ''
    case 'due_date':
      return task.due_date || ''
    case 'assignee':
      return assigneeLabel(task, getUser)
    case 'tags':
      return parseTags(task)
    case 'project':
      return task.project_title || task.project || ''
    case 'team':
      return task.team_title || task.team || ''
    case 'modified':
      return task.modified && dayjs ? dayjs(task.modified).format('YYYY-MM-DD HH:mm') : task.modified || ''
    case 'created_by':
      return getUser(task.owner)?.full_name || task.owner || ''
    case 'description':
      return (task.description || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
    case 'start_date':
      return task.start_date || ''
    case 'sprint':
      return task.sprint || ''
    case 'comments_count':
      return task.comments_count ?? ''
    default:
      return task[key] ?? ''
  }
}

export function downloadTasksSpreadsheet(tasks, selectedColumnKeys, helpers) {
  const defs = EXPORT_COLUMNS.filter((col) => selectedColumnKeys.includes(col.key))
  if (!defs.length) return

  const header = defs.map((col) => escapeCsv(col.label)).join(',')
  const rows = (tasks || []).map((task) =>
    defs.map((col) => escapeCsv(formatTaskValue(task, col.key, helpers))).join(','),
  )
  const csv = `\ufeff${[header, ...rows].join('\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  const stamp = helpers.dayjs ? helpers.dayjs().format('YYYY-MM-DD') : 'export'
  link.href = url
  link.download = `gameplan-tasks-${stamp}.csv`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
