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

# Statuses that should never receive due/overdue reminders.
CLOSED_TASK_STATUSES = frozenset({"Done", "Cancelled", "Not a Bug"})


def assignee_users_from_doc(doc) -> set:
	"""All User ids that should be treated as assignees for this task document."""
	if not doc:
		return set()
	users = set()
	assignees = doc.get("assignees") if isinstance(doc, dict) else getattr(doc, "assignees", None)
	for row in assignees or []:
		u = row.get("user") if isinstance(row, dict) else getattr(row, "user", None)
		if u:
			users.add(u)
	at = doc.get("assigned_to") if isinstance(doc, dict) else getattr(doc, "assigned_to", None)
	if at:
		users.add(at)
	return users


def enrich_task_rows_with_assignees(rows: list):
	if not rows:
		return
	# Parent `name` from SQL can be int (autoincrement) while child.parent is str — must match keys.
	names = []
	for r in rows:
		n = r.get("name")
		if n is None:
			continue
		ns = str(n).strip()
		if ns:
			names.append(ns)
	if not names:
		return
	by_parent = frappe._dict()
	# Use ORM so the Link column `user` is quoted correctly (raw `select user` can
	# mis-resolve vs MySQL's USER() function and collapse/wrong values).
	for r in frappe.get_all(
		"GP Task Assignee",
		filters={"parent": ["in", names]},
		fields=["parent", "user"],
		order_by="parent asc, idx asc",
	):
		by_parent.setdefault(str(r.parent), []).append(r.user)
	for row in rows:
		key = str(row.get("name")).strip() if row.get("name") is not None else ""
		users = list(by_parent.get(key, []))
		at = row.get("assigned_to")
		if at and at not in users:
			users.insert(0, at)
		if not users and at:
			users = [at]
		row["assignee_users"] = users


def parse_task_tags(raw: str | None) -> list[str]:
	return [tag.strip() for tag in (raw or "").split(",") if tag.strip()]


def append_descendant_task_rows(rows: list, fields):
	if not rows:
		return rows

	seen = {str(row.name) for row in rows if row.get("name") is not None}
	parent_names = list(seen)
	descendants = []
	fetch_fields = fields or ["*"]

	while parent_names:
		children = frappe.get_all(
			"GP Task",
			filters={"parent_task": ["in", parent_names]},
			fields=fetch_fields,
			order_by="creation asc",
		)
		parent_names = []
		for child in children:
			child_name = str(child.name)
			if child_name in seen:
				continue
			if not can_access_team(child.get("team")):
				continue
			seen.add(child_name)
			parent_names.append(child_name)
			descendants.append(child)

	if descendants:
		enrich_task_rows_with_assignees(descendants)
		rows.extend(descendants)
	return rows


class GPTask(HasMentions, HasActivity, Document):
	on_delete_cascade = ["GP Comment", "GP Activity", "GP Task Team Link"]
	on_delete_set_null = ["GP Notification"]
	activities = ["Task Value Changed"]
	mentions_field = "description"

	def before_validate(self):
		users = []
		seen = set()
		for row in self.assignees or []:
			u = row.user
			if u and u not in seen:
				seen.add(u)
				users.append(u)
		if not users and self.assigned_to:
			users = [self.assigned_to]

		self.assignees = []
		for u in users:
			self.append("assignees", {"user": u})

		self.assigned_to = users[0] if users else None
		self.sync_completion_from_status()

	def sync_completion_from_status(self):
		"""Keep is_completed aligned with terminal statuses so schedulers skip closed work."""
		if self.status in CLOSED_TASK_STATUSES:
			if not self.is_completed:
				self.is_completed = 1
			if not self.completed_at:
				self.completed_at = frappe.utils.now_datetime()
			if not self.completed_by and frappe.session.user not in (None, "Guest"):
				self.completed_by = frappe.session.user
			return

		if self.is_new() or not self.has_value_changed("status"):
			return

		prev = self.get_doc_before_save()
		if prev and prev.status in CLOSED_TASK_STATUSES:
			self.is_completed = 0
			self.completed_at = None
			self.completed_by = None

	def before_insert(self):
		if not self.task_type:
			self.task_type = "Task"
		if not self.status:
			self.status = "Backlog"

	def after_insert(self):
		self.update_tasks_count(1)
		self.notify_assignment()

	def on_update(self):
		self.sync_tasks_count_on_project_change()
		self.notify_assignment()
		self.update_project_progress()
		self.notify_mentions()
		self.log_value_updates()
		self.update_search_index()
		self.clear_schedule_notifications_if_closed()

	def clear_schedule_notifications_if_closed(self):
		is_closed = self.status in CLOSED_TASK_STATUSES or self.is_completed
		if not is_closed:
			return

		prev = self.get_doc_before_save()
		if not prev:
			return

		was_closed = prev.status in CLOSED_TASK_STATUSES or prev.is_completed
		if was_closed:
			return

		GPNotification.clear_task_schedule_notifications(self.name)

	def log_value_updates(self):
		fields = ["title", "description", "task_type", "status", "priority", "due_date", "project"]
		prev_doc = self.get_doc_before_save()
		for field in fields:
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
		old_assignees = sorted(assignee_users_from_doc(prev_doc)) if prev_doc else []
		new_assignees = sorted(assignee_users_from_doc(self))
		if old_assignees != new_assignees:
			self.log_activity(
				"Task Value Changed",
				data={
					"field": "assignees",
					"field_label": _("Assignees"),
					"old_value": old_assignees,
					"new_value": new_assignees,
				},
			)

	def update_search_index(self):
		if self.has_value_changed("title") or self.has_value_changed("description"):
			search = GameplanSearch()
			search.index_doc(self)

	def on_trash(self):
		search = GameplanSearch()
		search.remove_doc(self)

	def after_delete(self):
		# Row is gone now, so the recount is accurate.
		self.update_tasks_count()

	def notify_assignment(self):
		current = assignee_users_from_doc(self)
		if not current:
			return
		prev_doc = self.get_doc_before_save()
		if prev_doc:
			previous = assignee_users_from_doc(prev_doc)
		else:
			previous = set()
		new_users = current - previous
		if not new_users:
			return

		from_user = frappe.session.user if frappe.session.user not in ("Guest", None) else self.owner
		assigner_name = get_fullname(from_user) if from_user else _("Someone")
		for assignee in new_users:
			if assignee == frappe.session.user:
				continue
			if previous:
				message = _("{0} reassigned this task to you: {1}").format(assigner_name, self.title)
			else:
				message = _("{0} assigned you a task: {1}").format(assigner_name, self.title)
			GPNotification.notify_task_user(self, assignee, message, "Task Assigned", from_user)

	def update_tasks_count(self, delta=1, project=None):
		# delta is ignored; recompute from source so the counter can't drift (or go negative).
		project = project or self.project
		if not project:
			return
		count = frappe.db.count("GP Task", {"project": project})
		frappe.db.set_value("GP Project", project, "tasks_count", count)

	def sync_tasks_count_on_project_change(self):
		if not self.has_value_changed("project"):
			return
		prev_doc = self.get_doc_before_save()
		old_project = prev_doc.project if prev_doc else None
		if old_project:
			self.update_tasks_count(project=old_project)
		if self.project:
			self.update_tasks_count()

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
				"source_project": source_project or self.project,
				"note": note,
			}
		).insert(ignore_permissions=True)
		gameplan.refetch_resource("Tasks")
		gameplan.refetch_resource("Linked Projects")
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
			gameplan.refetch_resource("Linked Projects")
		return self.get_linked_teams()


def has_permission(doc, user, ptype):
	if ptype != "delete":
		return None
	if user == "Administrator" or doc.owner == user:
		return True
	roles = frappe.get_roles(user)
	return bool({"Gameplan Admin", "System Manager"} & set(roles))


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
	assigned_to_filter = filters.pop("assigned_to", None)
	linked_team = filters.pop("linked_team", None)
	linked_project = filters.pop("linked_project", None)
	tag_filter = filters.pop("tag", None)
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
	Task = frappe.qb.DocType(doctype)
	if linked_team:
		if not can_access_team(linked_team):
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		Link = frappe.qb.DocType("GP Task Team Link")
		linked_tasks = frappe.qb.from_(Link).select(Link.task).where(Link.team == linked_team)
		if linked_project:
			linked_tasks = linked_tasks.where(Link.source_project == linked_project)
			query = query.where(Task.name.isin(linked_tasks))
		else:
			query = query.where((Task.team == linked_team) | (Task.name.isin(linked_tasks)))
		if task_order_by:
			query = apply_task_order_by(query, Task, task_order_by)
	if assigned_or_owner:
		Assignee = frappe.qb.DocType("GP Task Assignee")
		sub = (
			frappe.qb.from_(Assignee)
			.select(Assignee.parent)
			.distinct()
			.where(Assignee.user == assigned_or_owner)
		)
		query = query.where(
			(Task.assigned_to == assigned_or_owner)
			| (Task.owner == assigned_or_owner)
			| (Task.name.isin(sub))
		)
	elif assigned_to_filter:
		Assignee = frappe.qb.DocType("GP Task Assignee")
		sub = (
			frappe.qb.from_(Assignee)
			.select(Assignee.parent)
			.distinct()
			.where(Assignee.user == assigned_to_filter)
		)
		query = query.where((Task.assigned_to == assigned_to_filter) | (Task.name.isin(sub)))
	if tag_filter:
		query = query.where(Task._user_tags.like(f"%{tag_filter}%"))
	rows = query.run(as_dict=True, debug=debug)
	if tag_filter:
		rows = [row for row in rows if tag_filter in parse_task_tags(row.get("_user_tags"))]
	enrich_task_rows_with_assignees(rows)
	return append_descendant_task_rows(rows, fields)


@frappe.whitelist()
def get_duplicate_candidates(
	title=None, assigned_to=None, assignees=None, team=None, project=None, limit=5
):
	if not title:
		return []

	filters = {
		"is_completed": 0,
		"status": ["not in", ["Done", "Cancelled"]],
		"title": ["like", f"%{title.strip()[:80]}%"],
	}

	user_set = set()
	if assignees:
		if isinstance(assignees, str):
			assignees = frappe.parse_json(assignees)
		for u in assignees:
			if u:
				user_set.add(u)
	if assigned_to:
		user_set.add(assigned_to)

	lim = frappe.utils.cint(limit) or 5
	max_fetch = lim * 25 if user_set else lim

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
		limit=max_fetch,
		order_by="modified desc",
	)
	enrich_task_rows_with_assignees(candidates)
	if user_set:
		filtered = []
		for task in candidates:
			task_users = set(task.get("assignee_users") or [])
			if task.get("assigned_to"):
				task_users.add(task["assigned_to"])
			if task_users & user_set:
				filtered.append(task)
		candidates = filtered

	team = team or frappe.db.get_value("GP Project", project, "team") if project else team
	out = [
		task
		for task in candidates
		if task.team != team and can_access_team(task.team)
	]
	return out[:lim]


@frappe.whitelist()
def link_task_to_team(task, team, source_project=None, note=None):
	if not task:
		frappe.throw(_("Task is required"))
	doc = frappe.get_doc("GP Task", task)
	return doc.link_team(team=team, source_project=source_project, note=note)


@frappe.whitelist()
def get_linked_projects(team=None):
	if team and not can_access_team(team):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	conditions = [
		"link.source_project is not null",
		"project.team != link.team",
	]
	if team:
		conditions.append("link.team = %(team)s")

	projects = frappe.db.sql(
		"""
		select
			project.name,
			project.title,
			project.team,
			link.team as linked_team,
			project.is_private,
			project.archived_at,
			count(distinct link.task) as tasks_count,
			0 as discussions_count,
			1 as is_linked_project
		from `tabGP Task Team Link` link
		inner join `tabGP Project` project
			on project.name = link.source_project
		where {conditions}
		group by project.name, link.team
		order by project.title asc
		""".format(conditions=" and ".join(conditions)),
		{"team": team},
		as_dict=True,
	)
	return [project for project in projects if can_access_team(project.linked_team)]


@frappe.whitelist()
def get_task_tags_for_doc(task_id):
	raw = frappe.db.get_value("GP Task", task_id, "_user_tags") or ""
	return parse_task_tags(raw)


@frappe.whitelist()
def get_task_tags(txt=""):
	rows = frappe.db.sql(
		"SELECT DISTINCT `_user_tags` FROM `tabGP Task` WHERE `_user_tags` IS NOT NULL AND `_user_tags` != ''",
		as_dict=False,
	)
	all_tags = set()
	for (raw,) in rows:
		for tag in raw.split(","):
			tag = tag.strip()
			if tag:
				all_tags.add(tag)
	txt = (txt or "").casefold()
	return sorted(t for t in all_tags if txt in t.casefold())


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
