# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# MIT License. See license.txt


import frappe


def execute():
	"""Copy legacy assigned_to into GP Task Assignee child rows when missing (no doc save = no assignment notifications)."""
	tasks = frappe.db.sql(
		"""
		select t.name, t.assigned_to
		from `tabGP Task` t
		where ifnull(t.assigned_to, '') != ''
		and not exists (
			select 1 from `tabGP Task Assignee` a where a.parent = t.name
		)
		""",
		as_dict=True,
	)
	for row in tasks:
		child = frappe.get_doc(
			{
				"doctype": "GP Task Assignee",
				"parent": row.name,
				"parenttype": "GP Task",
				"parentfield": "assignees",
				"user": row.assigned_to,
			}
		)
		child.insert(ignore_permissions=True)
