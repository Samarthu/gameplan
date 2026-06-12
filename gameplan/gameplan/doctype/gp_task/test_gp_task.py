# Copyright (c) 2022, Frappe Technologies Pvt Ltd and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from gameplan.task_notifications import send_task_due_notifications


class TestGPTask(FrappeTestCase):
	def test_cancelled_task_does_not_create_due_notification(self):
		user = frappe.session.user
		task = frappe.get_doc(
			{
				"doctype": "GP Task",
				"title": "Cancelled task should not notify",
				"status": "Cancelled",
				"due_date": getdate(),
				"assigned_to": user,
			}
		).insert(ignore_permissions=True)

		send_task_due_notifications()

		self.assertFalse(
			frappe.db.exists(
				"GP Notification",
				{
					"task": task.name,
					"to_user": user,
					"type": ["in", ["Task Due Soon", "Task Overdue"]],
				},
			)
		)

	def test_cancelled_task_clears_existing_overdue_notification(self):
		from frappe.utils import add_days, getdate

		user = frappe.session.user
		task = frappe.get_doc(
			{
				"doctype": "GP Task",
				"title": "Overdue task to cancel",
				"status": "Todo",
				"due_date": add_days(getdate(), -1),
				"assigned_to": user,
			}
		).insert(ignore_permissions=True)

		send_task_due_notifications()

		self.assertTrue(
			frappe.db.exists(
				"GP Notification",
				{
					"task": task.name,
					"to_user": user,
					"type": "Task Overdue",
					"read": 0,
				},
			)
		)

		task.status = "Cancelled"
		task.save(ignore_permissions=True)

		self.assertFalse(
			frappe.db.exists(
				"GP Notification",
				{
					"task": task.name,
					"to_user": user,
					"type": "Task Overdue",
					"read": 0,
				},
			)
		)
