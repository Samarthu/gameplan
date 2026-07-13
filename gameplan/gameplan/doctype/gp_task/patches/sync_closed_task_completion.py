import frappe

from gameplan.gameplan.doctype.gp_task.gp_task import CLOSED_TASK_STATUSES


def execute():
	"""Backfill is_completed for tasks already in a closed status."""
	closed = tuple(CLOSED_TASK_STATUSES)
	frappe.db.sql(
		"""
		update `tabGP Task`
		set is_completed = 1
		where is_completed = 0
			and status in %s
		""",
		(closed,),
	)
