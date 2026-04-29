# Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_fullname

from gameplan.extends.client import check_permissions
from gameplan.gameplan.doctype.gp_notification.gp_notification import GPNotification
from gameplan.mixins.activity import HasActivity
from gameplan.mixins.mentions import HasMentions
from gameplan.search import GameplanSearch


class GPTask(HasMentions, HasActivity, Document):
	on_delete_cascade = ["GP Comment", "GP Activity"]
	on_delete_set_null = ["GP Notification"]
	activities = ["Task Value Changed"]
	mentions_field = "description"

	def before_insert(self):
		if not self.status:
			self.status = "Backlog"

	def after_insert(self):
		self.update_tasks_count(1)
		self.notify_assignment()

	def on_update(self):
		self.notify_assignment()
		self.update_project_progress()
		self.notify_mentions()
		self.log_value_updates()
		self.update_search_index()

	def log_value_updates(self):
		fields = ["title", "description", "status", "priority", "assigned_to", "due_date", "project"]
		for field in fields:
			prev_doc = self.get_doc_before_save()
			if prev_doc and str(self.get(field)) != str(prev_doc.get(field)):
				self.log_activity(
					"Task Value Changed",
					data={
						"field": field,
						"field_label": self.meta.get_label(field),
						"old_value": prev_doc.get(field),
						"new_value": self.get(field),
					},
				)

	def update_search_index(self):
		if self.has_value_changed("title") or self.has_value_changed("description"):
			search = GameplanSearch()
			search.index_doc(self)

	def on_trash(self):
		self.update_tasks_count(-1)
		search = GameplanSearch()
		search.remove_doc(self)

	def notify_assignment(self):
		assignee = self.assigned_to
		if not assignee:
			return
		prev = self.get_doc_before_save()
		if prev is not None and prev.get("assigned_to") == assignee:
			return
		if assignee == frappe.session.user:
			return

		from_user = frappe.session.user if frappe.session.user not in ("Guest", None) else self.owner
		assigner_name = get_fullname(from_user) if from_user else _("Someone")
		if prev is not None and prev.get("assigned_to"):
			message = _("{0} reassigned this task to you: {1}").format(assigner_name, self.title)
		else:
			message = _("{0} assigned you a task: {1}").format(assigner_name, self.title)

		GPNotification.notify_task_user(self, assignee, message, "Task Assigned", from_user)

	def update_tasks_count(self, delta=1):
		if not self.project:
			return
		current_tasks_count = frappe.db.get_value("GP Project", self.project, "tasks_count") or 0
		frappe.db.set_value("GP Project", self.project, "tasks_count", current_tasks_count + delta)

	def update_project_progress(self):
		if self.project and self.has_value_changed("is_completed"):
			frappe.get_doc("GP Project", self.project).update_progress()

	@frappe.whitelist()
	def track_visit(self):
		GPNotification.clear_notifications(task=self.name)


@frappe.whitelist()
def get_list(
	fields=None,
	filters: dict | None = None,
	order_by=None,
	start=0,
	limit=20,
	group_by=None,
	parent=None,
	debug=False,
):
	doctype = "GP Task"
	check_permissions(doctype, parent)
	assigned_or_owner = filters.pop("assigned_or_owner", None)
	query = frappe.qb.get_query(
		table=doctype,
		fields=fields,
		filters=filters,
		order_by=order_by,
		offset=start,
		limit=limit,
		group_by=group_by,
	)
	if assigned_or_owner:
		Task = frappe.qb.DocType(doctype)
		query = query.where((Task.assigned_to == assigned_or_owner) | (Task.owner == assigned_or_owner))
	return query.run(as_dict=True, debug=debug)
