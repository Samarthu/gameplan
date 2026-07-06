# Copyright (c) Frappe Technologies Pvt. Ltd. and contributors
# Daily reminders for GP Task due dates (scheduled via hooks.scheduler_events).

import frappe
from frappe import _

from gameplan.gameplan.doctype.gp_notification.gp_notification import (
	GPNotification,
	TASK_SCHEDULE_NOTIFICATION_TYPES,
)

def dismiss_stale_task_schedule_notifications():
	"""Mark due/overdue notifications as read for closed or cancelled tasks."""
	type_placeholders = ", ".join(["%s"] * len(TASK_SCHEDULE_NOTIFICATION_TYPES))
	frappe.db.sql(
		f"""
		update `tabGP Notification` n
		inner join `tabGP Task` t on t.name = n.task
		set n.read = 1
		where n.read = 0
			and n.type in ({type_placeholders})
			and (
				t.is_completed = 1
				or t.status in ('Done', 'Cancelled')
			)
		""",
		TASK_SCHEDULE_NOTIFICATION_TYPES,
	)


def already_sent_today(task_name: str, notif_type: str, to_user: str) -> bool:
	from datetime import timedelta

	start = frappe.utils.now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
	end = start + timedelta(days=1)
	return bool(
		frappe.db.exists(
			"GP Notification",
			[
				["task", "=", task_name],
				["type", "=", notif_type],
				["to_user", "=", to_user],
				["creation", ">=", start],
				["creation", "<", end],
			],
		)
	)


def _task_assignee_user_ids(doc) -> list[str]:
	users = []
	if getattr(doc, "assigned_to", None):
		users.append(doc.assigned_to)
	for row in doc.assignees or []:
		if row.user and row.user not in users:
			users.append(row.user)
	return users


def send_task_due_notifications():
	"""Notify assignees when tasks are due tomorrow, due today, or overdue (runs daily)."""
	from frappe.utils import add_days, formatdate, getdate

	dismiss_stale_task_schedule_notifications()

	today_d = getdate()
	tomorrow_d = add_days(today_d, 1)

	def iter_task_names_with_assignees(due_date, op):
		assert op in ("=", "<")
		return frappe.db.sql(
			f"""
			select name from `tabGP Task` t
			where is_completed = 0
			and coalesce(status, '') not in ('Done', 'Cancelled')
			and due_date is not null
			and due_date {op} %(due)s
			and (
				ifnull(assigned_to, '') != ''
				or exists (select 1 from `tabGP Task Assignee` a where a.parent = t.name)
			)
			""",
			{"due": due_date},
			pluck="name",
		)

	for row in iter_task_names_with_assignees(tomorrow_d, "="):
		doc = frappe.get_doc("GP Task", row)
		message = _('Your task "{0}" is due tomorrow ({1}).').format(doc.title, formatdate(doc.due_date))
		for to_user in _task_assignee_user_ids(doc):
			if already_sent_today(row, "Task Due Soon", to_user):
				continue
			GPNotification.notify_task_user(doc, to_user, message, "Task Due Soon", None)

	for row in iter_task_names_with_assignees(today_d, "="):
		doc = frappe.get_doc("GP Task", row)
		message = _('Your task "{0}" is due today.').format(doc.title)
		for to_user in _task_assignee_user_ids(doc):
			if already_sent_today(row, "Task Due Soon", to_user):
				continue
			GPNotification.notify_task_user(doc, to_user, message, "Task Due Soon", None)

	for row in iter_task_names_with_assignees(today_d, "<"):
		doc = frappe.get_doc("GP Task", row)
		message = _('Your task "{0}" is overdue (due {1}).').format(doc.title, formatdate(doc.due_date))
		for to_user in _task_assignee_user_ids(doc):
			if already_sent_today(row, "Task Overdue", to_user):
				continue
			GPNotification.notify_task_user(doc, to_user, message, "Task Overdue", None)
