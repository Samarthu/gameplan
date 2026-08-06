# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, get_datetime, getdate, now_datetime, today

OPEN_TASK_STATUSES = ("Backlog", "Todo", "In Progress", "Reopen", "Ready for Testing", "Hold", "QA Accepted", "Live", "Under Testing", "Under Code Review", "Ready to Merge")
STALE_TASK_STATUSES = ("In Progress", "Ready for Testing", "Under Testing")

DEFAULT_RED_OVERDUE = 5
DEFAULT_AMBER_OVERDUE = 1
DEFAULT_STALE_TASK_DAYS = 14
DEFAULT_STALE_PROJECT_DAYS = 14
DEFAULT_SPRINT_MIN_COMPLETION_PCT = 70


def _get_settings() -> dict:
	if not frappe.db.exists("DocType", "GP Settings"):
		return {}
	return frappe.get_cached_doc("GP Settings").as_dict()


def _get_thresholds() -> dict:
	settings = _get_settings()
	return {
		"red_overdue": frappe.utils.cint(settings.get("health_red_overdue") or DEFAULT_RED_OVERDUE),
		"amber_overdue_max": frappe.utils.cint(settings.get("health_red_overdue") or DEFAULT_RED_OVERDUE) - 1,
		"amber_overdue_min": frappe.utils.cint(settings.get("health_amber_overdue") or DEFAULT_AMBER_OVERDUE),
		"stale_task_days": frappe.utils.cint(settings.get("stale_task_days") or DEFAULT_STALE_TASK_DAYS),
		"stale_project_days": frappe.utils.cint(settings.get("stale_project_days") or DEFAULT_STALE_PROJECT_DAYS),
		"sprint_min_completion_pct": flt(
			settings.get("sprint_min_completion_pct") or DEFAULT_SPRINT_MIN_COMPLETION_PCT
		),
	}


def can_access_executive_dashboard(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in ("Administrator",) or "System Manager" in frappe.get_roles(user):
		return True
	if "Gameplan Admin" in frappe.get_roles(user):
		return True
	settings = _get_settings()
	if not frappe.utils.cint(settings.get("enable_executive_dashboard", 1)):
		return False
	for row in settings.get("executive_dashboard_users") or []:
		if row.get("user") == user:
			return True
	return False


@frappe.whitelist()
def can_access_executive_dashboard_api() -> bool:
	return can_access_executive_dashboard()


def _require_executive_access():
	if not can_access_executive_dashboard():
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _week_bounds(week_start: str | None = None) -> tuple:
	if week_start:
		start = getdate(week_start)
	else:
		start = getdate(today())
		start = add_days(start, -start.weekday())
	end = add_days(start, 6)
	return start, end


def compute_team_health(metrics: dict, thresholds: dict | None = None) -> str:
	thresholds = thresholds or _get_thresholds()
	red_overdue = thresholds["red_overdue"]
	amber_min = thresholds["amber_overdue_min"]
	amber_max = thresholds.get("amber_overdue_max") or (red_overdue - 1)

	overdue = frappe.utils.cint(metrics.get("overdue_count") or 0)
	stale = frappe.utils.cint(metrics.get("stale_count") or 0)
	at_risk_goals = frappe.utils.cint(metrics.get("at_risk_goals") or 0)
	sprint_slip = metrics.get("sprint_slip")
	stale_projects = frappe.utils.cint(metrics.get("stale_projects") or 0)

	if overdue >= red_overdue or at_risk_goals > 0 or sprint_slip:
		return "red"
	if overdue >= amber_min or stale >= 3 or stale_projects > 0:
		return "amber"
	if overdue > 0 and overdue <= amber_max:
		return "amber"
	return "green"


def _open_task_filters(team: str | None = None) -> dict:
	filters = {
		"is_completed": 0,
		"status": ["not in", ["Done", "Cancelled"]],
	}
	if team:
		filters["team"] = team
	return filters


@frappe.whitelist()
def get_ceo_cockpit_data(week_start: str | None = None) -> dict:
	_require_executive_access()
	thresholds = _get_thresholds()
	week_start_date, week_end_date = _week_bounds(week_start)
	stale_task_cutoff = add_days(today(), -thresholds["stale_task_days"])
	stale_project_cutoff = add_days(today(), -thresholds["stale_project_days"])
	today_date = getdate(today())

	teams = frappe.get_all(
		"GP Team",
		filters={"archived_at": ["is", "not set"]},
		fields=["name", "title", "lead", "icon", "is_private", "modified"],
		order_by="title asc",
	)

	team_names = [t.name for t in teams]
	overdue_by_team = _count_overdue_by_team(team_names, today_date)
	stale_by_team = _count_stale_by_team(team_names, stale_task_cutoff)
	completed_by_team = _count_completed_by_team(team_names, week_start_date, week_end_date)
	created_by_team = _count_created_by_team(team_names, week_start_date, week_end_date)
	at_risk_by_team = _count_at_risk_goals_by_team(team_names)
	stale_projects_by_team = _count_stale_projects_by_team(team_names, stale_project_cutoff)
	sprints_by_team = _active_sprints_by_team(team_names)
	sprint_stats = _sprint_completion_stats(list(sprints_by_team.values()))

	team_rows = []
	for team in teams:
		tid = team.name
		sprint = sprints_by_team.get(tid)
		sprint_slip = False
		sprint_payload = None
		if sprint:
			stats = sprint_stats.get(sprint.name, {"total": 0, "done": 0})
			total = stats["total"]
			done = stats["done"]
			pct = (done / total * 100) if total else 0
			end = sprint.end_date and getdate(sprint.end_date)
			sprint_slip = bool(
				end
				and end < today_date
				and pct < thresholds["sprint_min_completion_pct"]
			)
			sprint_payload = {
				"name": sprint.name,
				"title": sprint.title,
				"status": sprint.status,
				"start_date": sprint.start_date,
				"end_date": sprint.end_date,
				"completion_pct": round(pct, 1),
				"tasks_total": total,
				"tasks_done": done,
				"sprint_slip": sprint_slip,
			}

		metrics = {
			"overdue_count": overdue_by_team.get(tid, 0),
			"stale_count": stale_by_team.get(tid, 0),
			"completed_7d": completed_by_team.get(tid, 0),
			"created_7d": created_by_team.get(tid, 0),
			"at_risk_goals": at_risk_by_team.get(tid, 0),
			"stale_projects": stale_projects_by_team.get(tid, 0),
			"sprint_slip": sprint_slip,
		}
		health = compute_team_health(metrics, thresholds)
		worst = _worst_project_for_team(tid, today_date)

		lead_name = None
		if team.lead:
			lead_name = frappe.db.get_value("User", team.lead, "full_name") or team.lead

		accountability, insight = _team_accountability(team.lead, health, metrics)

		team_rows.append(
			{
				"name": tid,
				"title": team.title,
				"icon": team.icon,
				"is_private": team.is_private,
				"lead": team.lead,
				"lead_name": lead_name,
				"health": health,
				"metrics": metrics,
				"active_sprint": sprint_payload,
				"worst_project": worst,
				"accountability": accountability,
				"insight": insight,
			}
		)

	health_order = {"red": 0, "amber": 1, "green": 2}
	team_rows.sort(key=lambda r: (health_order.get(r["health"], 9), r["title"]))

	initiatives = _build_initiatives(team_names, teams, today_date, at_risk_by_team)
	escalations = _build_escalations(team_rows, initiatives, today_date)
	people = _build_people_performance(
		team_names, week_start_date, week_end_date, today_date, stale_task_cutoff
	)
	unassigned_overdue = _count_unassigned_overdue(today_date)
	strategic_priorities = _build_strategic_priorities(
		team_names, teams, week_start_date, week_end_date, today_date, stale_task_cutoff
	)
	weekly_momentum = _build_weekly_momentum(
		team_rows, team_names, week_start_date, week_end_date, today_date
	)
	decisions_required = _build_decisions_required(
		team_rows, strategic_priorities, escalations, today_date
	)
	summary = _build_org_summary(
		team_rows, people, unassigned_overdue, weekly_momentum, strategic_priorities, decisions_required
	)
	lead_accountability = _build_lead_accountability(team_rows)
	management_insights = _build_management_insights(
		summary, team_rows, people, lead_accountability, unassigned_overdue, decisions_required
	)

	settings = _get_settings()
	return {
		"week": {
			"start": str(week_start_date),
			"end": str(week_end_date),
		},
		"links": {
			"control_dashboard": settings.get("control_dashboard_url") or "",
			"weekly_scorecard": settings.get("weekly_scorecard_url") or "",
		},
		"summary": summary,
		"weekly_momentum": weekly_momentum,
		"strategic_priorities": strategic_priorities,
		"decisions_required": decisions_required,
		"management_insights": management_insights,
		"lead_accountability": lead_accountability,
		"people": people,
		"teams": team_rows,
		"initiatives": initiatives[:10],
		"escalations": escalations,
		"generated_at": str(now_datetime()),
	}


def _count_overdue_by_team(team_names: list, today_date) -> dict:
	if not team_names:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT team, COUNT(*) AS cnt
		FROM `tabGP Task`
		WHERE team IN %(teams)s
			AND is_completed = 0
			AND status NOT IN ('Done', 'Cancelled')
			AND due_date IS NOT NULL
			AND due_date < %(today)s
		GROUP BY team
		""",
		{"teams": team_names, "today": today_date},
		as_dict=True,
	)
	return {r.team: r.cnt for r in rows}


def _count_stale_by_team(team_names: list, stale_cutoff) -> dict:
	if not team_names:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT team, COUNT(*) AS cnt
		FROM `tabGP Task`
		WHERE team IN %(teams)s
			AND is_completed = 0
			AND status IN %(statuses)s
			AND modified < %(cutoff)s
		GROUP BY team
		""",
		{
			"teams": team_names,
			"statuses": STALE_TASK_STATUSES,
			"cutoff": stale_cutoff,
		},
		as_dict=True,
	)
	return {r.team: r.cnt for r in rows}


def _count_completed_by_team(team_names: list, week_start, week_end) -> dict:
	if not team_names:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT team, COUNT(*) AS cnt
		FROM `tabGP Task`
		WHERE team IN %(teams)s
			AND is_completed = 1
			AND completed_at >= %(start)s
			AND completed_at < %(end)s
		GROUP BY team
		""",
		{
			"teams": team_names,
			"start": get_datetime(week_start),
			"end": get_datetime(add_days(week_end, 1)),
		},
		as_dict=True,
	)
	return {r.team: r.cnt for r in rows}


def _count_created_by_team(team_names: list, week_start, week_end) -> dict:
	if not team_names:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT team, COUNT(*) AS cnt
		FROM `tabGP Task`
		WHERE team IN %(teams)s
			AND creation >= %(start)s
			AND creation < %(end)s
		GROUP BY team
		""",
		{
			"teams": team_names,
			"start": get_datetime(week_start),
			"end": get_datetime(add_days(week_end, 1)),
		},
		as_dict=True,
	)
	return {r.team: r.cnt for r in rows}


def _count_at_risk_goals_by_team(team_names: list) -> dict:
	if not team_names:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT p.team, COUNT(g.name) AS cnt
		FROM `tabGP Project Goal` g
		INNER JOIN `tabGP Project` p ON p.name = g.parent
		WHERE p.team IN %(teams)s
			AND p.status = 'Open'
			AND (p.archived_at IS NULL OR p.archived_at = '')
			AND g.status = 'At Risk'
		GROUP BY p.team
		""",
		{"teams": team_names},
		as_dict=True,
	)
	return {r.team: r.cnt for r in rows}


def _count_stale_projects_by_team(team_names: list, stale_cutoff) -> dict:
	if not team_names:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT team, COUNT(*) AS cnt
		FROM `tabGP Project`
		WHERE team IN %(teams)s
			AND status = 'Open'
			AND (archived_at IS NULL OR archived_at = '')
			AND modified < %(cutoff)s
		GROUP BY team
		""",
		{"teams": team_names, "cutoff": stale_cutoff},
		as_dict=True,
	)
	return {r.team: r.cnt for r in rows}


def _active_sprints_by_team(team_names: list) -> dict:
	if not team_names:
		return {}
	rows = frappe.get_all(
		"GP Sprint",
		filters={"team": ["in", team_names], "status": "Active"},
		fields=["name", "title", "team", "status", "start_date", "end_date"],
		order_by="start_date desc",
	)
	out = {}
	for row in rows:
		if row.team not in out:
			out[row.team] = row
	return out


def _sprint_completion_stats(sprint_names: list) -> dict:
	sprint_names = [s for s in sprint_names if s]
	if not sprint_names:
		return {}
	rows = frappe.db.sql(
		"""
		SELECT sprint,
			COUNT(*) AS total,
			SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) AS done
		FROM `tabGP Task`
		WHERE sprint IN %(sprints)s
		GROUP BY sprint
		""",
		{"sprints": sprint_names},
		as_dict=True,
	)
	return {r.sprint: {"total": r.total, "done": r.done} for r in rows}


def _worst_project_for_team(team: str, today_date) -> dict | None:
	rows = frappe.db.sql(
		"""
		SELECT p.name, p.title, p.progress, p.modified,
			(
				SELECT COUNT(*)
				FROM `tabGP Task` t
				WHERE t.project = p.name
					AND t.is_completed = 0
					AND t.status NOT IN ('Done', 'Cancelled')
					AND t.due_date IS NOT NULL
					AND t.due_date < %(today)s
			) AS overdue_tasks
		FROM `tabGP Project` p
		WHERE p.team = %(team)s
			AND p.status = 'Open'
			AND (p.archived_at IS NULL OR p.archived_at = '')
		ORDER BY overdue_tasks DESC, p.modified ASC
		LIMIT 1
		""",
		{"team": team, "today": today_date},
		as_dict=True,
	)
	if not rows:
		return None
	r = rows[0]
	return {
		"name": r.name,
		"title": r.title,
		"progress": flt(r.progress),
		"overdue_tasks": r.overdue_tasks,
	}


def _build_initiatives(team_names: list, teams: list, today_date, at_risk_by_team: dict) -> list:
	if not team_names:
		return []
	team_lead = {t.name: t.lead for t in teams}
	projects = frappe.get_all(
		"GP Project",
		filters={
			"team": ["in", team_names],
			"status": "Open",
			"archived_at": ["is", "not set"],
		},
		fields=["name", "title", "team", "progress", "modified"],
		order_by="modified asc",
	)
	if not projects:
		return []

	project_names = [p.name for p in projects]
	goals = frappe.get_all(
		"GP Project Goal",
		filters={"parent": ["in", project_names]},
		fields=["parent", "title", "status"],
	)
	goals_by_project: dict[str, list] = {}
	for g in goals:
		goals_by_project.setdefault(g.parent, []).append(
			{"title": g.title, "status": g.status}
		)

	overdue_by_project = {}
	rows = frappe.db.sql(
		"""
		SELECT project, COUNT(*) AS cnt
		FROM `tabGP Task`
		WHERE project IN %(projects)s
			AND is_completed = 0
			AND status NOT IN ('Done', 'Cancelled')
			AND due_date IS NOT NULL
			AND due_date < %(today)s
		GROUP BY project
		""",
		{"projects": project_names, "today": today_date},
		as_dict=True,
	)
	for r in rows:
		overdue_by_project[r.project] = r.cnt

	initiatives = []
	for p in projects:
		goal_list = goals_by_project.get(p.name, [])
		at_risk = sum(1 for g in goal_list if g["status"] == "At Risk")
		overdue = overdue_by_project.get(p.name, 0)
		recent_cutoff = get_datetime(add_days(today(), -7))
		if not at_risk and not overdue and get_datetime(p.modified) >= recent_cutoff:
			continue
		lead = team_lead.get(p.team)
		initiatives.append(
			{
				"name": p.name,
				"title": p.title,
				"team": p.team,
				"lead": lead,
				"progress": flt(p.progress),
				"goals": goal_list,
				"at_risk_goals": at_risk,
				"overdue_tasks": overdue,
				"modified": str(p.modified),
				"severity": at_risk * 1000 + overdue,
			}
		)

	initiatives.sort(key=lambda x: (-x["severity"], x["modified"]))
	return initiatives


def _days_since(value, today_date) -> int | None:
	if not value:
		return None
	return max((today_date - getdate(value)).days, 0)


def _priority_health(at_risk_goals: int, overdue: int, stale: int, progress: float, days_since_update: int | None) -> str:
	if at_risk_goals or overdue >= 5 or (days_since_update is not None and days_since_update >= 21):
		return "red"
	if overdue or stale >= 3 or progress < 25 or (days_since_update is not None and days_since_update >= 14):
		return "amber"
	return "green"


def _priority_decision(priority: dict) -> str:
	if not priority.get("lead"):
		return _("Assign an accountable owner.")
	if priority.get("at_risk_goals"):
		return _("Review recovery plan or change scope.")
	if priority.get("goals_total") == 0:
		return _("Define the business outcome and success goals.")
	if priority.get("overdue_tasks"):
		return _("Decide what to unblock, delegate, or de-prioritize.")
	if priority.get("stale_tasks"):
		return _("Ask owner for current status and next milestone.")
	if priority.get("days_since_update") is not None and priority.get("days_since_update") >= 14:
		return _("Require a weekly update before review.")
	if priority.get("open_tasks") == 0 and priority.get("done_goals") < priority.get("goals_total"):
		return _("Confirm next tasks needed to move the goal.")
	return _("No CEO decision needed right now.")


def _build_strategic_priorities(
	team_names: list,
	teams: list,
	week_start,
	week_end,
	today_date,
	stale_cutoff,
	limit: int = 8,
) -> list[dict]:
	if not team_names:
		return []

	team_map = {t.name: t for t in teams}
	projects = frappe.get_all(
		"GP Project",
		filters={
			"team": ["in", team_names],
			"status": "Open",
			"archived_at": ["is", "not set"],
		},
		fields=["name", "title", "team", "progress", "modified"],
		order_by="modified asc",
	)
	if not projects:
		return []

	project_names = [p.name for p in projects]
	goals = frappe.get_all(
		"GP Project Goal",
		filters={"parent": ["in", project_names]},
		fields=["parent", "title", "status"],
	)
	goals_by_project: dict[str, list] = {}
	for g in goals:
		goals_by_project.setdefault(g.parent, []).append({"title": g.title, "status": g.status})

	task_rows = frappe.db.sql(
		"""
		SELECT project,
			COUNT(*) AS total_tasks,
			SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) AS done_tasks,
			SUM(CASE WHEN is_completed = 0 AND status NOT IN ('Done', 'Cancelled') THEN 1 ELSE 0 END) AS open_tasks,
			SUM(CASE WHEN is_completed = 0 AND status NOT IN ('Done', 'Cancelled')
				AND due_date IS NOT NULL AND due_date < %(today)s THEN 1 ELSE 0 END) AS overdue_tasks,
			SUM(CASE WHEN is_completed = 0 AND status IN %(stale_statuses)s
				AND modified < %(stale_cutoff)s THEN 1 ELSE 0 END) AS stale_tasks,
			SUM(CASE WHEN is_completed = 1 AND completed_at >= %(start)s AND completed_at < %(end)s
				THEN 1 ELSE 0 END) AS completed_week
		FROM `tabGP Task`
		WHERE project IN %(projects)s
		GROUP BY project
		""",
		{
			"projects": project_names,
			"today": today_date,
			"stale_statuses": STALE_TASK_STATUSES,
			"stale_cutoff": stale_cutoff,
			"start": get_datetime(week_start),
			"end": get_datetime(add_days(week_end, 1)),
		},
		as_dict=True,
	)
	task_stats = {r.project: r for r in task_rows}

	priorities = []
	for project in projects:
		team = team_map.get(project.team)
		goal_list = goals_by_project.get(project.name, [])
		goals_total = len(goal_list)
		at_risk_goals = sum(1 for g in goal_list if g["status"] == "At Risk")
		done_goals = sum(1 for g in goal_list if g["status"] == "Done")
		stats = task_stats.get(project.name) or frappe._dict()
		overdue = frappe.utils.cint(stats.get("overdue_tasks") or 0)
		stale = frappe.utils.cint(stats.get("stale_tasks") or 0)
		completed_week = frappe.utils.cint(stats.get("completed_week") or 0)
		open_tasks = frappe.utils.cint(stats.get("open_tasks") or 0)
		total_tasks = frappe.utils.cint(stats.get("total_tasks") or 0)
		progress = flt(project.progress)
		days_since_update = _days_since(project.modified, today_date)
		health = _priority_health(at_risk_goals, overdue, stale, progress, days_since_update)
		coverage_gap = goals_total == 0 or (open_tasks == 0 and done_goals < goals_total)
		severity = (
			at_risk_goals * 1000
			+ (300 if not getattr(team, "lead", None) else 0)
			+ overdue * 30
			+ stale * 10
			+ (days_since_update or 0)
			+ (100 if coverage_gap else 0)
		)
		row = {
			"name": project.name,
			"title": project.title,
			"team": project.team,
			"team_title": getattr(team, "title", project.team),
			"team_icon": getattr(team, "icon", ""),
			"lead": getattr(team, "lead", None),
			"lead_name": frappe.db.get_value("User", getattr(team, "lead", None), "full_name")
			if getattr(team, "lead", None)
			else None,
			"progress": progress,
			"health": health,
			"goals_total": goals_total,
			"at_risk_goals": at_risk_goals,
			"done_goals": done_goals,
			"open_tasks": open_tasks,
			"total_tasks": total_tasks,
			"overdue_tasks": overdue,
			"stale_tasks": stale,
			"completed_week": completed_week,
			"days_since_update": days_since_update,
			"coverage_gap": coverage_gap,
			"modified": str(project.modified),
			"severity": severity,
		}
		row["decision_needed"] = _priority_decision(row)
		priorities.append(row)

	priorities.sort(key=lambda x: (-x["severity"], x["title"]))
	return priorities[:limit]


def _build_weekly_momentum(team_rows: list, team_names: list, week_start, week_end, today_date) -> dict:
	created = sum(frappe.utils.cint((t.get("metrics") or {}).get("created_7d") or 0) for t in team_rows)
	completed = sum(frappe.utils.cint((t.get("metrics") or {}).get("completed_7d") or 0) for t in team_rows)
	overdue = sum(frappe.utils.cint((t.get("metrics") or {}).get("overdue_count") or 0) for t in team_rows)
	open_total = 0
	due_this_week_open = 0
	urgent_high_overdue = 0
	if team_names:
		result = frappe.db.sql(
			"""
			SELECT
				COUNT(*) AS open_total,
				SUM(CASE WHEN due_date >= %(start)s AND due_date < %(end)s THEN 1 ELSE 0 END) AS due_this_week_open,
				SUM(CASE WHEN due_date IS NOT NULL AND due_date < %(today)s
					AND priority IN ('Urgent', 'High') THEN 1 ELSE 0 END) AS urgent_high_overdue
			FROM `tabGP Task`
			WHERE team IN %(teams)s
				AND is_completed = 0
				AND status NOT IN ('Done', 'Cancelled')
			""",
			{
				"teams": team_names,
				"start": get_datetime(week_start),
				"end": get_datetime(add_days(week_end, 1)),
				"today": today_date,
			},
			as_dict=True,
		)
		if result:
			open_total = frappe.utils.cint(result[0].open_total or 0)
			due_this_week_open = frappe.utils.cint(result[0].due_this_week_open or 0)
			urgent_high_overdue = frappe.utils.cint(result[0].urgent_high_overdue or 0)

	net_flow = completed - created
	completion_ratio = round((completed / created * 100), 1) if created else (100 if completed else 0)
	return {
		"created_week": created,
		"completed_week": completed,
		"net_flow": net_flow,
		"completion_ratio": completion_ratio,
		"open_total": open_total,
		"overdue_total": overdue,
		"due_this_week_open": due_this_week_open,
		"urgent_high_overdue": urgent_high_overdue,
	}


def _decision_item(kind: str, title: str, action: str, severity: str, **kwargs) -> dict:
	item = {
		"type": kind,
		"title": title,
		"action": action,
		"severity": severity,
	}
	item.update(kwargs)
	return item


def _build_decisions_required(
	team_rows: list,
	strategic_priorities: list,
	escalations: list,
	today_date,
	limit: int = 10,
) -> list[dict]:
	decisions = []
	for team in team_rows:
		if not team.get("lead"):
			decisions.append(
				_decision_item(
					"missing_owner",
					_("Assign owner for {0}").format(team.get("title")),
					_("Choose a Team Lead so execution accountability is clear."),
					"red",
					team=team.get("name"),
					score=900,
				)
			)
		if (team.get("active_sprint") or {}).get("sprint_slip"):
			sprint = team.get("active_sprint") or {}
			decisions.append(
				_decision_item(
					"sprint_slip",
					_("Recover sprint: {0}").format(sprint.get("title") or team.get("title")),
					_("Decide whether to extend, de-scope, or reassign sprint work."),
					"red",
					team=team.get("name"),
					score=850,
				)
			)

	for priority in strategic_priorities:
		if priority.get("at_risk_goals"):
			score = 800 + priority.get("at_risk_goals", 0) * 50
		elif priority.get("coverage_gap"):
			score = 650
		elif priority.get("overdue_tasks"):
			score = 600 + priority.get("overdue_tasks", 0) * 10
		elif priority.get("days_since_update") is not None and priority.get("days_since_update") >= 14:
			score = 500 + priority.get("days_since_update", 0)
		else:
			continue
		decisions.append(
			_decision_item(
				"priority_decision",
				priority.get("title"),
				priority.get("decision_needed"),
				priority.get("health"),
				team=priority.get("team"),
				project=priority.get("name"),
				score=score,
				meta=_("{0} · {1}% progress · updated {2} day(s) ago").format(
					priority.get("team_title"),
					priority.get("progress"),
					priority.get("days_since_update") if priority.get("days_since_update") is not None else 0,
				),
			)
		)

	for item in escalations:
		if item.get("type") == "overdue_task" and (
			item.get("priority") in ("Urgent", "High") or frappe.utils.cint(item.get("days_late") or 0) > 7
		):
			decisions.append(
				_decision_item(
					"urgent_overdue",
					item.get("title"),
					_("Unblock, reassign, or explicitly de-prioritize this overdue work."),
					item.get("health") or "amber",
					team=item.get("team"),
					project=item.get("project"),
					task=item.get("task"),
					score=450 + frappe.utils.cint(item.get("days_late") or 0),
					meta=_("{0} day(s) overdue").format(item.get("days_late") or 0),
				)
			)

	seen = set()
	unique = []
	for item in sorted(decisions, key=lambda d: (-d.get("score", 0), d.get("title") or "")):
		key = (item.get("type"), item.get("team"), item.get("project"), item.get("task"), item.get("title"))
		if key in seen:
			continue
		seen.add(key)
		item.pop("score", None)
		unique.append(item)
	return unique[:limit]


def _build_escalations(team_rows: list, initiatives: list, today_date) -> list:
	escalations = []
	for team in team_rows:
		if team["health"] == "red":
			escalations.append(
				{
					"type": "team_red",
					"title": _("Team {0} needs attention").format(team["title"]),
					"owner_user": team.get("lead"),
					"team": team["name"],
					"project": None,
					"task": None,
					"days_late": None,
					"health": "red",
				}
			)

	for init in initiatives:
		for goal in init.get("goals") or []:
			if goal.get("status") == "At Risk":
				escalations.append(
					{
						"type": "goal_at_risk",
						"title": _("Goal at risk: {0} — {1}").format(init["title"], goal["title"]),
						"owner_user": init.get("lead"),
						"team": init["team"],
						"project": init["name"],
						"task": None,
						"days_late": None,
						"health": "amber",
					}
				)

	overdue_tasks = frappe.db.sql(
		"""
		SELECT name, title, team, project, assigned_to, due_date, priority
		FROM `tabGP Task`
		WHERE is_completed = 0
			AND status NOT IN ('Done', 'Cancelled')
			AND due_date IS NOT NULL
			AND due_date < %(today)s
		ORDER BY
			FIELD(priority, 'Urgent', 'High', 'Medium', 'Low', ''),
			due_date ASC
		LIMIT 15
		""",
		{"today": today_date},
		as_dict=True,
	)
	for task in overdue_tasks:
		due = getdate(task.due_date)
		days_late = (today_date - due).days
		escalations.append(
			{
				"type": "overdue_task",
				"title": task.title,
				"owner_user": task.assigned_to,
				"team": task.team,
				"project": task.project,
				"task": task.name,
				"days_late": days_late,
				"health": "red" if days_late > 7 or task.priority == "Urgent" else "amber",
				"priority": task.priority,
			}
		)

	return escalations


def _team_accountability(lead: str | None, health: str, metrics: dict) -> tuple[str, str]:
	if not lead:
		return "missing_lead", _("No Team Lead assigned — assign a lead on the team overview page.")

	overdue = frappe.utils.cint(metrics.get("overdue_count") or 0)
	completed = frappe.utils.cint(metrics.get("completed_7d") or 0)
	at_risk = frappe.utils.cint(metrics.get("at_risk_goals") or 0)

	if health == "red":
		if completed == 0 and overdue > 0:
			return (
				"underperforming",
				_("Lead accountable: {0} overdue tasks, nothing closed this week.").format(overdue),
			)
		if at_risk:
			return "underperforming", _("Lead accountable: team has at-risk goals and {0} overdue tasks.").format(
				overdue
			)
		return "underperforming", _("Lead accountable: team health is red ({0} overdue).").format(overdue)

	if health == "amber":
		return "watch", _("Watch list: {0} overdue, {1} completed this week.").format(overdue, completed)

	return "on_track", _("On track: {0} tasks completed this week.").format(completed)


def _user_display_names(users: set[str]) -> dict[str, str]:
	if not users:
		return {}
	rows = frappe.get_all(
		"User",
		filters={"name": ["in", list(users)]},
		fields=["name", "full_name"],
	)
	return {r.name: r.full_name or r.name for r in rows}


def _person_performance_status(overdue: int, stale: int, completed_7d: int) -> str:
	if overdue >= 5 or (overdue >= 3 and completed_7d == 0):
		return "underperforming"
	if overdue >= 1 or stale >= 3:
		return "struggling"
	return "on_track"


def _build_people_performance(
	team_names: list,
	week_start,
	week_end,
	today_date,
	stale_cutoff,
	limit: int = 15,
) -> list[dict]:
	overdue_rows = frappe.db.sql(
		"""
		SELECT assigned_to AS user, COUNT(*) AS overdue_count
		FROM `tabGP Task`
		WHERE is_completed = 0
			AND status NOT IN ('Done', 'Cancelled')
			AND due_date IS NOT NULL
			AND due_date < %(today)s
			AND assigned_to IS NOT NULL
			AND assigned_to != ''
		GROUP BY assigned_to
		ORDER BY overdue_count DESC
		LIMIT %(limit)s
		""",
		{"today": today_date, "limit": limit},
		as_dict=True,
	)
	if not overdue_rows:
		return []

	users = {r.user for r in overdue_rows}
	stale_by_user = {}
	if users:
		stale_rows = frappe.db.sql(
			"""
			SELECT assigned_to AS user, COUNT(*) AS stale_count
			FROM `tabGP Task`
			WHERE assigned_to IN %(users)s
				AND is_completed = 0
				AND status IN %(statuses)s
				AND modified < %(cutoff)s
			GROUP BY assigned_to
			""",
			{"users": list(users), "statuses": STALE_TASK_STATUSES, "cutoff": stale_cutoff},
			as_dict=True,
		)
		stale_by_user = {r.user: r.stale_count for r in stale_rows}

	completed_by_user = {}
	completed_rows = frappe.db.sql(
		"""
		SELECT COALESCE(NULLIF(completed_by, ''), assigned_to) AS user, COUNT(*) AS completed_7d
		FROM `tabGP Task`
		WHERE is_completed = 1
			AND completed_at >= %(start)s
			AND completed_at < %(end)s
			AND COALESCE(NULLIF(completed_by, ''), assigned_to) IN %(users)s
		GROUP BY user
		""",
		{
			"users": list(users),
			"start": get_datetime(week_start),
			"end": get_datetime(add_days(week_end, 1)),
		},
		as_dict=True,
	)
	for r in completed_rows:
		if r.user:
			completed_by_user[r.user] = r.completed_7d

	team_rows = frappe.db.sql(
		"""
		SELECT assigned_to AS user, GROUP_CONCAT(DISTINCT team ORDER BY team SEPARATOR ', ') AS teams
		FROM `tabGP Task`
		WHERE assigned_to IN %(users)s
			AND is_completed = 0
			AND team IS NOT NULL
			AND team != ''
		GROUP BY assigned_to
		""",
		{"users": list(users)},
		as_dict=True,
	)
	teams_by_user = {r.user: r.teams for r in team_rows}

	names = _user_display_names(users)
	people = []
	for row in overdue_rows:
		user = row.user
		overdue = row.overdue_count
		stale = stale_by_user.get(user, 0)
		completed = completed_by_user.get(user, 0)
		status = _person_performance_status(overdue, stale, completed)
		if status == "on_track":
			continue
		people.append(
			{
				"user": user,
				"full_name": names.get(user, user),
				"status": status,
				"overdue_count": overdue,
				"stale_count": stale,
				"completed_7d": completed,
				"teams": teams_by_user.get(user) or "",
				"insight": _person_insight(status, overdue, stale, completed),
			}
		)

	status_order = {"underperforming": 0, "struggling": 1}
	people.sort(key=lambda p: (status_order.get(p["status"], 9), -p["overdue_count"]))
	return people


def _person_insight(status: str, overdue: int, stale: int, completed: int) -> str:
	if status == "underperforming":
		if completed == 0:
			return _("Not performing: {0} overdue tasks, none completed this week.").format(overdue)
		return _("Not performing: {0} overdue tasks despite {1} completed this week.").format(overdue, completed)
	return _("Struggling: {0} overdue, {1} stale in progress.").format(overdue, stale)


def _count_unassigned_overdue(today_date) -> int:
	result = frappe.db.sql(
		"""
		SELECT COUNT(*) FROM `tabGP Task`
		WHERE is_completed = 0
			AND status NOT IN ('Done', 'Cancelled')
			AND due_date IS NOT NULL
			AND due_date < %(today)s
			AND (assigned_to IS NULL OR assigned_to = '')
		""",
		{"today": today_date},
	)
	return frappe.utils.cint(result[0][0]) if result else 0


def _build_org_summary(
	team_rows: list,
	people: list,
	unassigned_overdue: int,
	weekly_momentum: dict | None = None,
	strategic_priorities: list | None = None,
	decisions_required: list | None = None,
) -> dict:
	by_health = {"red": 0, "amber": 0, "green": 0}
	teams_without_lead = 0
	leads_underperforming = 0
	total_overdue = 0
	total_completed = 0
	weekly_momentum = weekly_momentum or {}
	strategic_priorities = strategic_priorities or []
	decisions_required = decisions_required or []

	for team in team_rows:
		by_health[team.get("health", "green")] = by_health.get(team.get("health", "green"), 0) + 1
		if not team.get("lead"):
			teams_without_lead += 1
		if team.get("accountability") in ("missing_lead", "underperforming"):
			leads_underperforming += 1
		metrics = team.get("metrics") or {}
		total_overdue += frappe.utils.cint(metrics.get("overdue_count") or 0)
		total_completed += frappe.utils.cint(metrics.get("completed_7d") or 0)

	return {
		"teams_total": len(team_rows),
		"teams_red": by_health.get("red", 0),
		"teams_amber": by_health.get("amber", 0),
		"teams_green": by_health.get("green", 0),
		"teams_without_lead": teams_without_lead,
		"leads_underperforming": leads_underperforming,
		"people_underperforming": sum(1 for p in people if p.get("status") == "underperforming"),
		"people_struggling": sum(1 for p in people if p.get("status") == "struggling"),
		"total_overdue": total_overdue,
		"total_completed_week": total_completed,
		"unassigned_overdue": unassigned_overdue,
		"strategic_priorities_red": sum(1 for p in strategic_priorities if p.get("health") == "red"),
		"strategic_priorities_amber": sum(1 for p in strategic_priorities if p.get("health") == "amber"),
		"decisions_pending": len(decisions_required),
		"net_flow": weekly_momentum.get("net_flow", 0),
		"open_total": weekly_momentum.get("open_total", 0),
	}


def _build_lead_accountability(team_rows: list) -> list[dict]:
	priority = {"missing_lead": 0, "underperforming": 1, "watch": 2, "on_track": 3}
	rows = []
	for team in team_rows:
		acc = team.get("accountability") or "on_track"
		if acc == "on_track":
			continue
		rows.append(
			{
				"team": team["name"],
				"team_title": team["title"],
				"team_icon": team.get("icon"),
				"health": team.get("health"),
				"lead": team.get("lead"),
				"lead_name": team.get("lead_name"),
				"accountability": acc,
				"insight": team.get("insight"),
				"metrics": team.get("metrics"),
			}
		)
	rows.sort(key=lambda r: (priority.get(r["accountability"], 9), r.get("team_title") or ""))
	return rows


def _build_management_insights(
	summary: dict,
	team_rows: list,
	people: list,
	lead_accountability: list,
	unassigned_overdue: int,
	decisions_required: list | None = None,
	limit: int = 12,
) -> list[dict]:
	insights = []
	decisions_required = decisions_required or []

	if decisions_required:
		insights.append(
			{
				"severity": "red" if any(d.get("severity") == "red" for d in decisions_required) else "amber",
				"text": _("{0} leadership decision(s) needed before the next review.").format(
					len(decisions_required)
				),
			}
		)

	if summary.get("strategic_priorities_red") or summary.get("strategic_priorities_amber"):
		insights.append(
			{
				"severity": "red" if summary.get("strategic_priorities_red") else "amber",
				"text": _("{0} strategic priority(ies) red, {1} amber.").format(
					summary.get("strategic_priorities_red") or 0,
					summary.get("strategic_priorities_amber") or 0,
				),
			}
		)

	if summary.get("net_flow", 0) < 0:
		insights.append(
			{
				"severity": "amber",
				"text": _("Execution debt grew this week: {0} more task(s) opened than closed.").format(
					abs(summary.get("net_flow"))
				),
			}
		)

	if summary.get("teams_without_lead"):
		insights.append(
			{
				"severity": "red",
				"text": _("{0} team(s) have no Team Lead — execution ownership is unclear.").format(
					summary["teams_without_lead"]
				),
			}
		)

	if summary.get("leads_underperforming"):
		insights.append(
			{
				"severity": "red",
				"text": _("{0} team lead(s) accountable for red/amber teams this week.").format(
					summary["leads_underperforming"]
				),
			}
		)

	for lead_row in lead_accountability[:4]:
		name = lead_row.get("lead_name") or _("Unassigned")
		insights.append(
			{
				"severity": "red" if lead_row.get("accountability") == "underperforming" else "amber",
				"text": _("{0} — {1}: {2}").format(
					lead_row.get("team_title"),
					name,
					lead_row.get("insight"),
				),
				"team": lead_row.get("team"),
				"lead": lead_row.get("lead"),
			}
		)

	if people:
		top = people[0]
		insights.append(
			{
				"severity": "red" if top.get("status") == "underperforming" else "amber",
				"text": _("Highest overdue load: {0} ({1} overdue tasks).").format(
					top.get("full_name"),
					top.get("overdue_count"),
				),
				"user": top.get("user"),
			}
		)

	if unassigned_overdue:
		insights.append(
			{
				"severity": "amber",
				"text": _("{0} overdue task(s) have no assignee.").format(unassigned_overdue),
			}
		)

	if summary.get("teams_red"):
		insights.append(
			{
				"severity": "red",
				"text": _("{0} team(s) in red — discuss only these in Monday review.").format(
					summary["teams_red"]
				),
			}
		)

	if not insights and team_rows:
		insights.append(
			{
				"severity": "green",
				"text": _("All teams have leads assigned and no critical execution gaps this week."),
			}
		)

	return insights[:limit]
