# Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_fullname
from pypika.enums import Order

import gameplan
from gameplan.extends.client import check_permissions
from gameplan.gameplan.doctype.gp_notification.gp_notification import GPNotification
from gameplan.mixins.activity import HasActivity
from gameplan.mixins.mentions import HasMentions
from gameplan.search import GameplanSearch


class GPTask(HasMentions, HasActivity, Document):
	on_delete_cascade = ["GP Comment", "GP Activity", "GP Task Team Link"]
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
	def get_linked_teams(self):
		linked_teams = frappe.db.get_all(
			"GP Task Team Link",
			filters={"task": self.name},
			fields=["name", "team", "team.title as team_title", "source_project", "note"],
			order_by="`tabGP Task Team Link`.`creation` asc",
		)
		return [team for team in linked_teams if can_access_team(team.team)]

	@frappe.whitelist()
	def link_team(self, team, source_project=None, note=None):
		if not team:
			frappe.throw(_("Team is required"))
		if not frappe.db.exists("GP Team", team):
			frappe.throw(_("Invalid team"))
		if not can_access_team(team):
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		if self.team == team:
			return self.get_linked_teams()

		existing = frappe.db.exists("GP Task Team Link", {"task": self.name, "team": team})
		if existing:
			return self.get_linked_teams()

		frappe.get_doc(
			{
				"doctype": "GP Task Team Link",
				"task": self.name,
				"team": team,
				"source_project": source_project,
				"note": note,
			}
		).insert(ignore_permissions=True)
		gameplan.refetch_resource("Tasks")
		return self.get_linked_teams()

	@frappe.whitelist()
	def unlink_team(self, team):
		if not team:
			frappe.throw(_("Team is required"))
		if not can_access_team(team):
			frappe.throw(_("Not permitted"), frappe.PermissionError)

		existing = frappe.db.exists("GP Task Team Link", {"task": self.name, "team": team})
		if existing:
			frappe.delete_doc("GP Task Team Link", existing, ignore_permissions=True)
			gameplan.refetch_resource("Tasks")
		return self.get_linked_teams()


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
	filters = filters or {}
	assigned_or_owner = filters.pop("assigned_or_owner", None)
	linked_team = filters.pop("linked_team", None)
	task_order_by = order_by
	if linked_team:
		order_by = None
	query = frappe.qb.get_query(
		table=doctype,
		fields=fields,
		filters=filters,
		order_by=order_by,
		offset=start,
		limit=limit,
		group_by=group_by,
	)
	if linked_team:
		if not can_access_team(linked_team):
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		Task = frappe.qb.DocType(doctype)
		Link = frappe.qb.DocType("GP Task Team Link")
		linked_tasks = (
			frappe.qb.from_(Link).select(Link.task).where(Link.team == linked_team)
		)
		query = query.where((Task.team == linked_team) | (Task.name.isin(linked_tasks)))
		if task_order_by:
			query = apply_task_order_by(query, Task, task_order_by)
	if assigned_or_owner:
		Task = frappe.qb.DocType(doctype)
		query = query.where((Task.assigned_to == assigned_or_owner) | (Task.owner == assigned_or_owner))
	return query.run(as_dict=True, debug=debug)


@frappe.whitelist()
def get_duplicate_candidates(title=None, assigned_to=None, team=None, project=None, limit=5):
	if not title:
		return []

	filters = {
		"is_completed": 0,
		"status": ["not in", ["Done", "Canceled"]],
		"title": ["like", f"%{title.strip()[:80]}%"],
	}
	if assigned_to:
		filters["assigned_to"] = assigned_to

	candidates = frappe.db.get_all(
		"GP Task",
		filters=filters,
		fields=[
			"name",
			"title",
			"assigned_to",
			"status",
			"team",
			"team.title as team_title",
			"project",
			"project.title as project_title",
			"modified",
		],
		limit=frappe.utils.cint(limit) or 5,
		order_by="modified desc",
	)
	team = team or frappe.db.get_value("GP Project", project, "team") if project else team
	return [
		task
		for task in candidates
		if task.team != team and can_access_team(task.team)
	]


@frappe.whitelist()
def link_task_to_team(task, team, source_project=None, note=None):
	if not task:
		frappe.throw(_("Task is required"))
	doc = frappe.get_doc("GP Task", task)
	return doc.link_team(team=team, source_project=source_project, note=note)


def can_access_team(team):
	if not team:
		return True
	if frappe.session.user == "Administrator":
		return True
	if not frappe.db.get_value("GP Team", team, "is_private"):
		return True
	if frappe.db.exists("GP Member", {"parenttype": "GP Team", "parent": team, "user": frappe.session.user}):
		return True
	if gameplan.is_guest() and frappe.db.exists(
		"GP Guest Access", {"team": team, "user": frappe.session.user}
	):
		return True
	return False


def apply_task_order_by(query, Task, order_by):
	parts = order_by.split()
	if not parts:
		return query
	field = parts[0]
	direction = parts[1].lower() if len(parts) > 1 else "asc"
	order = Order.desc if direction == "desc" else Order.asc
	return query.orderby(Task[field], order=order)
