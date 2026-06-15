# Copyright (c) 2022, Frappe Technologies Pvt Ltd and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch


class TestGPProject(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.team = frappe.get_doc({"doctype": "GP Team", "title": "Merge Test Team"}).insert(
			ignore_permissions=True
		)

	def tearDown(self):
		frappe.db.rollback()

	def test_merge_with_project_moves_linked_records(self):
		source = frappe.get_doc(
			{"doctype": "GP Project", "title": "Merge Source", "team": self.team.name}
		).insert(ignore_permissions=True)
		target = frappe.get_doc(
			{"doctype": "GP Project", "title": "Merge Target", "team": self.team.name}
		).insert(ignore_permissions=True)
		task = frappe.get_doc(
			{
				"doctype": "GP Task",
				"title": "Merge task",
				"project": source.name,
				"team": self.team.name,
				"status": "Backlog",
			}
		).insert(ignore_permissions=True)
		page = frappe.get_doc(
			{
				"doctype": "GP Page",
				"title": "Merge page",
				"project": source.name,
				"team": self.team.name,
				"content": "Hello",
			}
		).insert(ignore_permissions=True)

		with patch("gameplan.notify_project_merged") as notify:
			result = source.merge_with_project(project=target.name)
			notify.assert_called_once()

		self.assertEqual(result, frappe.utils.cstr(target.name))
		self.assertFalse(frappe.db.exists("GP Project", source.name))
		self.assertEqual(frappe.db.get_value("GP Task", task.name, "project"), frappe.utils.cstr(target.name))
		self.assertEqual(frappe.db.get_value("GP Page", page.name, "project"), frappe.utils.cstr(target.name))
