# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, today

OPEN_TASK_STATUSES = ("Backlog", "Todo", "In Progress", "Reopen", "Ready for Testing", "Hold", "QA Accepted", "Live", "Under Testing", "Under Code Review", "Ready to Merge")

TASK_STATUSES = (
	"Backlog",
	"Todo",
	"In Progress",
	"Reopen",
	"Ready for Testing",
	"Hold",
	"QA Accepted",
	"Live",
	"Under Testing",
	"Under Code Review",
	"Ready to Merge",
	"Done",
	"Cancelled",
	"Not a Bug",
)

TASK_TYPES = (
	"Task",
	"Feature",
	"Milestone",
	"Improvement",
	"Bug",
	"Event",
	"Form Response",
	"Meeting Note",
	"Request",
	"Approval",
	"Follow-up",
	"Documentation",
	"Support",
)


def _resolve_range(from_date: str | None, to_date: str | None) -> tuple:
	"""Default to the last 7 days when no explicit range is provided."""
	end = getdate(to_date) if to_date else getdate(today())
	start = getdate(from_date) if from_date else add_days(end, -6)
	if start > end:
		start, end = end, start
	return start, end


def _tasks_for_user(user: str) -> list[str]:
	"""Task names where the user is primary or secondary assignee."""
	names: set[str] = {
		row.parent
		for row in frappe.get_all(
			"GP Task Assignee", filters={"user": user}, fields=["parent"], limit_page_length=0
		)
	}
	for row in frappe.get_all(
		"GP Task", filters={"assigned_to": user}, fields=["name"], limit_page_length=0
	):
		names.add(row.name)
	return list(names)


def _tasks_for_users(users: list[str]) -> list[str]:
	"""Union of task names for multiple assignees."""
	names: set[str] = set()
	for user in users:
		names.update(_tasks_for_user(user))
	return list(names)


def _parse_people(people) -> list[str]:
	"""Accept a single user id, JSON array, or list."""
	if not people:
		return []
	if isinstance(people, str):
		parsed = frappe.parse_json(people)
		if isinstance(parsed, list):
			return [u for u in parsed if u]
		return [people]
	if isinstance(people, (list, tuple)):
		return [u for u in people if u]
	return []


def _build_filters(start, end, team, project, people) -> dict:
	filters = {"creation": ["between", [str(start), str(end) + " 23:59:59"]]}
	if team:
		filters["team"] = team
	if project:
		filters["project"] = project
	if people:
		filters["assigned_to"] = people
	return filters


def _reporting_tree(user: str) -> list[str]:
	"""Return the user plus every descendant in their reporting line (recursive)."""
	profiles = frappe.get_all(
		"GP User Profile", fields=["name", "user", "reports_to"], limit_page_length=0
	)
	by_user = {p.user: p for p in profiles}
	# Map a manager's profile -> list of direct reportee users.
	children: dict[str, list[str]] = {}
	for p in profiles:
		if p.reports_to:
			children.setdefault(p.reports_to, []).append(p.user)

	my_profile = by_user.get(user)
	result = [user]
	if not my_profile:
		return result

	queue = [my_profile.name]
	seen = {my_profile.name}
	while queue:
		profile_name = queue.pop()
		for reportee_user in children.get(profile_name, []):
			if reportee_user in result:
				continue
			result.append(reportee_user)
			reportee_profile = by_user.get(reportee_user)
			if reportee_profile and reportee_profile.name not in seen:
				seen.add(reportee_profile.name)
				queue.append(reportee_profile.name)
	return result


@frappe.whitelist()
def get_dashboard_data(
	from_date: str | None = None,
	to_date: str | None = None,
	team: str | None = None,
	project: str | None = None,
	people: str | None = None,
) -> dict:
	start, end = _resolve_range(from_date, to_date)
	# Gameplan Admins see everything; everyone else is scoped to their reporting line.
	is_admin = "Gameplan Admin" in frappe.get_roles()
	tree = None if is_admin else _reporting_tree(frappe.session.user)
	filters = _build_filters(start, end, team, project, None)

	people_list = _parse_people(people)
	if people_list:
		# A person can be a secondary assignee, so match the assignees child table.
		filters["name"] = ["in", _tasks_for_users(people_list) or [""]]
	elif tree is not None:
		# No explicit person → scope to me + my whole reporting line (admins: unscoped).
		filters["assigned_to"] = ["in", tree]

	tasks = frappe.get_all(
		"GP Task",
		filters=filters,
		fields=[
			"name",
			"title",
			"status",
			"task_type",
			"team",
			"project",
			"assigned_to",
			"is_completed",
			"due_date",
			"creation",
			"completed_at",
			"sprint",
		],
		limit_page_length=0,
	)

	total = len(tasks)
	completed = [t for t in tasks if t.is_completed]
	open_tasks = [t for t in tasks if t.status in OPEN_TASK_STATUSES]
	today_date = getdate(today())
	overdue = [
		t for t in open_tasks if t.due_date and getdate(t.due_date) < today_date
	]

	# Average days from creation to completion (maps to "resolution time").
	durations = []
	for t in completed:
		if t.completed_at and t.creation:
			delta = getdate(t.completed_at) - getdate(t.creation)
			durations.append(delta.days)
	avg_resolution_days = round(sum(durations) / len(durations), 1) if durations else 0

	completion_rate = round((len(completed) / total) * 100, 1) if total else 0

	summary = {
		"total_tasks": total,
		"completion_rate": completion_rate,
		"open_tasks": len(open_tasks),
		"overdue_tasks": len(overdue),
		"avg_resolution_days": avg_resolution_days,
	}

	# Map each task -> its assignees (child table), batched.
	task_assignees: dict[str, list[str]] = {}
	if tasks:
		for row in frappe.get_all(
			"GP Task Assignee",
			filters={"parent": ["in", [t.name for t in tasks]]},
			fields=["parent", "user"],
			limit_page_length=0,
		):
			if row.user:
				task_assignees.setdefault(str(row.parent), []).append(row.user)

	# Resolve display names + images for every assignee once (batch lookup).
	assignee_users = list(
		{t.assigned_to for t in tasks if t.assigned_to}
		| {u for users in task_assignees.values() for u in users}
	)
	name_map = {}
	image_map = {}
	if assignee_users:
		for p in frappe.get_all(
			"GP User Profile",
			filters={"user": ["in", assignee_users]},
			fields=["user", "full_name", "image"],
			limit_page_length=0,
		):
			name_map[p.user] = p.full_name or p.user
			image_map[p.user] = p.image or None

	# Resolve team and project titles.
	team_names = list({t.team for t in tasks if t.team})
	team_title_map = {}
	if team_names:
		for row in frappe.get_all(
			"GP Team", filters={"name": ["in", team_names]}, fields=["name", "title"]
		):
			team_title_map[str(row.name)] = row.title

	project_names = list({t.project for t in tasks if t.project})
	project_title_map = {}
	if project_names:
		for row in frappe.get_all(
			"GP Project", filters={"name": ["in", project_names]}, fields=["name", "title"]
		):
			project_title_map[str(row.name)] = row.title

	task_list = [
		{
			"name": t.name,
			"title": t.title,
			"status": t.status,
			"task_type": t.task_type,
			"assigned_to": t.assigned_to,
			"assigned_to_name": name_map.get(t.assigned_to, t.assigned_to),
			"assigned_to_image": image_map.get(t.assigned_to),
			"assignees": [
				{"user": u, "name": name_map.get(u, u), "image": image_map.get(u)}
				for u in (task_assignees.get(str(t.name)) or ([t.assigned_to] if t.assigned_to else []))
			],
			"due_date": str(t.due_date) if t.due_date else None,
			"project": t.project,
			"project_title": project_title_map.get(str(t.project), t.project),
			"team": t.team,
			"team_title": team_title_map.get(str(t.team), t.team),
		}
		for t in tasks
	]
	task_list.sort(key=lambda t: (t["due_date"] or "9999", t["title"] or ""))

	return {
		"range": {"from": str(start), "to": str(end)},
		"summary": summary,
		"activity": _activity_series(tasks, start, end),
		"by_status": _group_count(tasks, "status", TASK_STATUSES),
		"by_team": _by_team(tasks),
		"by_type": _group_count(tasks, "task_type", TASK_TYPES),
		"by_sprint": _by_sprint(tasks),
		"due_date_revisions": _due_date_revisions(tasks),
		"on_hold": _on_hold(tasks),
		"team_options": _team_options(start, end, tree),
		"project_options": _project_options(start, end, team, tree),
		"people_options": _people_in_scope(start, end, team, project, tree),
		"task_list": task_list,
	}


def _team_options(start, end, tree) -> list[dict]:
	"""Teams that appear in the reporting-tree task set for the date range,
	regardless of visibility — so totals reconcile. Private teams are flagged."""
	scope = _build_filters(start, end, None, None, None)
	if tree is not None:
		scope["assigned_to"] = ["in", tree]
	names = {
		t.team
		for t in frappe.get_all("GP Task", filters=scope, fields=["team"], limit_page_length=0)
		if t.team
	}
	if not names:
		return []
	teams = frappe.get_all(
		"GP Team", filters={"name": ["in", list(names)]}, fields=["name", "title", "is_private"]
	)
	options = [
		{"value": t.name, "label": t.title, "is_private": bool(t.is_private)} for t in teams
	]
	options.sort(key=lambda o: o["label"].lower())
	return options


def _project_options(start, end, team, tree) -> list[dict]:
	"""Projects in scope, cascaded by the selected team. Private projects flagged."""
	scope = _build_filters(start, end, team, None, None)
	if tree is not None:
		scope["assigned_to"] = ["in", tree]
	names = {
		t.project
		for t in frappe.get_all("GP Task", filters=scope, fields=["project"], limit_page_length=0)
		if t.project
	}
	if not names:
		return []
	projects = frappe.get_all(
		"GP Project",
		filters={"name": ["in", list(names)]},
		fields=["name", "title", "is_private", "team"],
	)
	options = [
		{"value": p.name, "label": p.title, "is_private": bool(p.is_private), "team": p.team}
		for p in projects
	]
	options.sort(key=lambda o: o["label"].lower())
	return options


def _by_sprint(tasks) -> dict:
	counts = {}
	for t in tasks:
		if not t.sprint:  # skip tasks with no sprint
			continue
		counts[t.sprint] = counts.get(t.sprint, 0) + 1
	titles = {}
	if counts:
		for row in frappe.get_all(
			"GP Sprint", filters={"name": ["in", list(counts)]}, fields=["name", "title"]
		):
			# GP Sprint has integer names while task.sprint is a string
			titles[str(row.name)] = row.title
	labels = sorted(counts, key=lambda k: counts[k], reverse=True)
	return {
		"labels": [titles.get(k, k) for k in labels],
		"datasets": [{"name": "Tasks", "values": [counts[k] for k in labels]}],
	}


def _people_in_scope(start, end, team, project, tree) -> list[dict]:
	"""People who have tasks in the current date/team/project scope.

	Includes both primary assignees (assigned_to) and secondary assignees
	(GP Task Assignee child table). Always lists the current user first."""
	me = frappe.session.user
	scope = _build_filters(start, end, team, project, None)
	if tree is not None:
		scope["assigned_to"] = ["in", tree]
	task_rows = frappe.get_all(
		"GP Task",
		filters=scope,
		fields=["name", "assigned_to"],
		limit_page_length=0,
	)
	assignees: set[str] = set()
	for row in task_rows:
		if row.assigned_to:
			assignees.add(row.assigned_to)
	task_names = [row.name for row in task_rows]
	if task_names:
		for row in frappe.get_all(
			"GP Task Assignee",
			filters={"parent": ["in", task_names]},
			fields=["user"],
			limit_page_length=0,
		):
			if row.user:
				assignees.add(row.user)
	assignees.add(me)  # always offer self

	names = {
		p.user: (p.full_name or p.user)
		for p in frappe.get_all(
			"GP User Profile",
			filters={"user": ["in", list(assignees)]},
			fields=["user", "full_name"],
			limit_page_length=0,
		)
	}
	options = [
		{"value": u, "label": names.get(u, u) + (" (You)" if u == me else "")}
		for u in assignees
	]
	options.sort(key=lambda o: (o["value"] != me, o["label"].lower()))
	return options


def _activity_series(tasks, start, end) -> dict:
	"""Created vs completed counts bucketed by day across the range."""
	created_by_day = {}
	completed_by_day = {}
	for t in tasks:
		c = getdate(t.creation)
		created_by_day[str(c)] = created_by_day.get(str(c), 0) + 1
		if t.completed_at:
			d = getdate(t.completed_at)
			if start <= d <= end:
				completed_by_day[str(d)] = completed_by_day.get(str(d), 0) + 1

	labels, created, done = [], [], []
	cursor = start
	while cursor <= end:
		key = str(cursor)
		labels.append(key)
		created.append(created_by_day.get(key, 0))
		done.append(completed_by_day.get(key, 0))
		cursor = add_days(cursor, 1)

	return {
		"labels": labels,
		"datasets": [
			{"name": "Created", "values": created},
			{"name": "Completed", "values": done},
		],
	}


def _group_count(tasks, field, known_values) -> dict:
	counts = {}
	for t in tasks:
		key = t.get(field) or "Unspecified"
		counts[key] = counts.get(key, 0) + 1
	# Preserve a stable, meaningful order; drop empty buckets.
	ordered = [v for v in known_values if counts.get(v)]
	extras = [k for k in counts if k not in known_values]
	labels = ordered + extras
	return {
		"labels": labels,
		"datasets": [{"name": "Tasks", "values": [counts[k] for k in labels]}],
	}


def _due_date_revisions(tasks, top_n=10) -> dict:
	"""Top tasks by number of due-date changes logged in GP Activity (data is a JSON string)."""
	if not tasks:
		return {"labels": [], "datasets": [{"name": "Revisions", "values": []}]}
	title_map = {str(t.name): t.title for t in tasks}
	counts = {}
	for row in frappe.get_all(
		"GP Activity",
		filters={
			"reference_doctype": "GP Task",
			"reference_name": ["in", list(title_map.keys())],
			"action": "Task Value Changed",
		},
		fields=["reference_name", "data"],
		limit_page_length=0,
	):
		data = frappe.parse_json(row.data) if row.data else {}
		if data.get("field") == "due_date":
			key = str(row.reference_name)
			counts[key] = counts.get(key, 0) + 1
	ranked = sorted(counts, key=lambda k: counts[k], reverse=True)[:top_n]
	return {
		"labels": [title_map.get(k, k) for k in ranked],
		"datasets": [{"name": "Revisions", "values": [counts[k] for k in ranked]}],
	}


def _on_hold(tasks) -> list[dict]:
	return [
		{"name": t.name, "title": t.title, "project": t.project}
		for t in tasks
		if t.status == "Hold"
	]


def _by_team(tasks) -> dict:
	counts = {}
	for t in tasks:
		key = t.team or "No team"
		counts[key] = counts.get(key, 0) + 1
	# Resolve team titles for display.
	titles = {}
	team_names = [k for k in counts if k != "No team"]
	if team_names:
		for row in frappe.get_all(
			"GP Team", filters={"name": ["in", team_names]}, fields=["name", "title"]
		):
			titles[row.name] = row.title
	labels = sorted(counts, key=lambda k: counts[k], reverse=True)
	return {
		"labels": [titles.get(k, k) for k in labels],
		"datasets": [{"name": "Tasks", "values": [counts[k] for k in labels]}],
	}
