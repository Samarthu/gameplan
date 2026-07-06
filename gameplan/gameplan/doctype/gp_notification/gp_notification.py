# Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import gameplan


TASK_SCHEDULE_NOTIFICATION_TYPES = ("Task Due Soon", "Task Overdue")


class GPNotification(Document):
	def after_insert(self):
		gameplan.refetch_resource("Unread Notifications Count", user=self.to_user)

	@staticmethod
	def clear_task_schedule_notifications(task, user=None):
		"""Dismiss due/overdue notifications when a task is closed or cancelled."""
		if not task:
			return

		filters = {
			"task": task,
			"type": ["in", list(TASK_SCHEDULE_NOTIFICATION_TYPES)],
			"read": 0,
		}
		if user:
			filters["to_user"] = user

		affected_users = set()
		for notification in frappe.get_all("GP Notification", filters=filters, pluck="name"):
			doc = frappe.get_doc("GP Notification", notification)
			affected_users.add(doc.to_user)
			doc.read = 1
			doc.save(ignore_permissions=True)

		for to_user in affected_users:
			gameplan.refetch_resource("Unread Notifications Count", user=to_user)

	@staticmethod
	def notify_task_user(task_doc, to_user, message, notif_type, from_user=None):
		frappe.get_doc(
			{
				"doctype": "GP Notification",
				"type": notif_type,
				"from_user": from_user,
				"to_user": to_user,
				"task": task_doc.name,
				"project": getattr(task_doc, "project", None),
				"team": getattr(task_doc, "team", None),
				"message": message,
			}
		).insert(ignore_permissions=True)

	@staticmethod
	def clear_notifications(discussion=None, comment=None, task=None, user=None):
		if not user:
			user = frappe.session.user
		filters = {"to_user": user}
		if discussion:
			filters["discussion"] = discussion
		if comment:
			filters["comment"] = comment
		if task:
			filters["task"] = task

		for notification in frappe.get_all("GP Notification", filters=filters):
			doc = frappe.get_doc("GP Notification", notification.name)
			doc.read = 1
			doc.save()

		gameplan.refetch_resource("Unread Notifications Count", user=user)
