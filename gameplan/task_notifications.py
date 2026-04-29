# Copyright (c) Frappe Technologies Pvt. Ltd. and contributors
# Daily reminders for GP Task due dates (scheduled via hooks.scheduler_events).

import frappe
from frappe import _

from gameplan.gameplan.doctype.gp_notification.gp_notification import GPNotification


def already_sent_today(task_name: str, notif_type: str) -> bool:
	from datetime import timedelta

	start = frappe.utils.now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
	end = start + timedelta(days=1)
	return bool(
		frappe.db.exists(
			"GP Notification",
			[
				["task", "=", task_name],
				["type", "=", notif_type],
				["creation", ">=", start],
				["creation", "<", end],
			],
		)
	)


def send_task_due_notifications():
	"""Notify assignees when tasks are due tomorrow, due today, or overdue (runs daily)."""
	from frappe.utils import add_days, formatdate, getdate

	today_d = getdate()
	tomorrow_d = add_days(today_d, 1)

	base_filters = {"is_completed": 0, "assigned_to": ["!=", ""]}

	for row in frappe.get_all(
		"GP Task",
		filters={**base_filters, "due_date": tomorrow_d},
		pluck="name",
	):
		if already_sent_today(row, "Task Due Soon"):
			continue
		doc = frappe.get_doc("GP Task", row)
		message = _('Your task "{0}" is due tomorrow ({1}).').format(doc.title, formatdate(doc.due_date))
		GPNotification.notify_task_user(doc, doc.assigned_to, message, "Task Due Soon", None)

	for row in frappe.get_all(
		"GP Task",
		filters={**base_filters, "due_date": today_d},
		pluck="name",
	):
		if already_sent_today(row, "Task Due Soon"):
			continue
		doc = frappe.get_doc("GP Task", row)
		message = _('Your task "{0}" is due today.').format(doc.title)
		GPNotification.notify_task_user(doc, doc.assigned_to, message, "Task Due Soon", None)

	for row in frappe.get_all(
		"GP Task",
		filters={**base_filters, "due_date": ("<", today_d)},
		pluck="name",
	):
		if already_sent_today(row, "Task Overdue"):
			continue
		doc = frappe.get_doc("GP Task", row)
		message = _('Your task "{0}" is overdue (due {1}).').format(doc.title, formatdate(doc.due_date))
		GPNotification.notify_task_user(doc, doc.assigned_to, message, "Task Overdue", None)
