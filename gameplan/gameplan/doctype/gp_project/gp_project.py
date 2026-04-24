# Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

from urllib.parse import urljoin

import frappe
import requests
from bs4 import BeautifulSoup
from frappe import _
from frappe.model.document import Document
from pypika.terms import ExistsCriterion

import gameplan
from gameplan.api import invite_by_email
from gameplan.gemoji import get_random_gemoji
from gameplan.mixins.archivable import Archivable
from gameplan.mixins.manage_members import ManageMembersMixin

DEFAULT_PROJECT_GOAL_LIMIT = 3


def get_max_project_goals() -> int:
	if frappe.db.exists("DocType", "GP Settings"):
		max_goals = frappe.db.get_single_value("GP Settings", "max_goals_per_project")
		# Backward compatibility if an environment already synced the previous field name.
		if max_goals is None:
			max_goals = frappe.db.get_single_value("GP Settings", "default_goal_limit")
		n = frappe.utils.cint(max_goals or DEFAULT_PROJECT_GOAL_LIMIT)
	else:
		n = DEFAULT_PROJECT_GOAL_LIMIT
	if n < 1:
		return 1
	return n


class GPProject(ManageMembersMixin, Archivable, Document):
	on_delete_cascade = [
		"GP Task",
		"GP Discussion",
		"GP Project Visit",
		"GP Followed Project",
		"GP Page",
		"GP Pinned Project",
	]
	on_delete_set_null = ["GP Notification"]

	@staticmethod
	def get_list_query(query):
		Project = frappe.qb.DocType("GP Project")
		Member = frappe.qb.DocType("GP Member")
		member_exists = (
			frappe.qb.from_(Member)
			.select(Member.name)
			.where(Member.parenttype == "GP Team")
			.where(Member.parent == Project.team)
			.where(Member.user == frappe.session.user)
		)
		query = query.where(
			(Project.is_private == 0) | ((Project.is_private == 1) & ExistsCriterion(member_exists))
		)
		if gameplan.is_guest():
			GuestAccess = frappe.qb.DocType("GP Guest Access")
			project_list = GuestAccess.select(GuestAccess.project).where(
				GuestAccess.user == frappe.session.user
			)
			query = query.where(Project.name.isin(project_list))
		return query

	def as_dict(self, *args, **kwargs) -> dict:
		d = super().as_dict(*args, **kwargs)
		max_goals = get_max_project_goals()
		d.max_goal_limit = max_goals
		d.goal_limit = self.goal_limit or min(DEFAULT_PROJECT_GOAL_LIMIT, max_goals)
		# summary
		total_tasks = frappe.db.count("GP Task", {"project": self.name})
		completed_tasks = frappe.db.count("GP Task", {"project": self.name, "is_completed": 1})
		pending_tasks = total_tasks - completed_tasks
		overdue_tasks = frappe.db.count(
			"GP Task",
			{"project": self.name, "is_completed": 0, "due_date": ("<", frappe.utils.today())},
		)
		d.summary = {
			"total_tasks": total_tasks,
			"completed_tasks": completed_tasks,
			"pending_tasks": pending_tasks,
			"overdue_tasks": overdue_tasks,
		}
		d.is_pinned = bool(
			frappe.db.exists("GP Pinned Project", {"project": self.name, "user": frappe.session.user})
		)
		return d

	def before_insert(self):
		if not self.goal_limit:
			self.goal_limit = min(DEFAULT_PROJECT_GOAL_LIMIT, get_max_project_goals())

		if not self.icon:
			self.icon = get_random_gemoji().emoji

		if not self.readme:
			self.readme = f"""<h3>Welcome to the {self.title} page!</h3>
			<p>You can add a brief introduction about this project, links,
			resources, and other important information here.</p>
			"""

		self.append(
			"members",
			{
				"user": frappe.session.user,
				"email": frappe.session.user,
				"role": "Project Owner",
				"status": "Accepted",
			},
		)

	def validate(self):
		max_goals = get_max_project_goals()
		default_goal_limit = min(DEFAULT_PROJECT_GOAL_LIMIT, max_goals)
		goal_limit = frappe.utils.cint(self.goal_limit or default_goal_limit)
		if goal_limit < 1 or goal_limit > max_goals:
			frappe.throw(
				_("Goal limit must be between 1 and {0}.").format(max_goals)
			)
		self.goal_limit = goal_limit

		if self.goals and len(self.goals) > goal_limit:
			frappe.throw(_("A project can have at most {0} goals.").format(goal_limit))

	def before_save(self):
		if frappe.db.get_value("GP Team", self.team, "is_private"):
			self.is_private = True

	def update_progress(self):
		result = frappe.db.get_all(
			"GP Task",
			filters={"project": self.name},
			fields=["sum(is_completed) as completed", "count(name) as total"],
		)[0]
		if result.total > 0:
			self.progress = (result.completed or 0) * 100 / result.total
			self.save()
			self.reload()

	def delete_group(self, group):
		tasks = frappe.db.count("GP Task", {"project": self.name, "status": group})
		if tasks > 0:
			frappe.throw(f"Group {group} cannot be deleted because it has {tasks} tasks")

		for state in self.task_states:
			if state.status == group:
				self.remove(state)
				self.save()
				break

	def get_activities(self):
		activities = []
		activities.append(
			{
				"type": "info",
				"title": "Project created",
				"date": self.creation,
				"user": self.owner,
			}
		)
		status_updates = frappe.db.get_all(
			"Team Project Status Update",
			{"project": self.name},
			["creation", "owner", "content", "status"],
			order_by="creation desc",
		)
		for status_update in status_updates:
			activities.append(
				{
					"type": "content",
					"title": "Status Update",
					"content": status_update.content,
					"status": status_update.status,
					"date": frappe.utils.get_datetime(status_update.creation),
					"user": status_update.owner,
				}
			)
		activities.sort(key=lambda x: x["date"], reverse=True)
		return activities

	@frappe.whitelist()
	def move_to_team(self, team):
		if not team or self.team == team:
			return
		self.team = team
		self.save()
		for doctype in ["GP Task", "GP Discussion"]:
			for name in frappe.db.get_all(doctype, {"project": self.name}, pluck="name"):
				doc = frappe.get_doc(doctype, name)
				doc.team = self.team
				doc.save()

	@frappe.whitelist()
	def merge_with_project(self, project=None):
		if not project or self.name == project:
			return
		if isinstance(project, str):
			project = int(project)
		if not frappe.db.exists("GP Project", project):
			frappe.throw(f'Invalid Project "{project}"')
		return self.rename(project, merge=True, validate_rename=False, force=True)

	@frappe.whitelist()
	def invite_guest(self, email):
		invite_by_email(email, role="Gameplan Guest", projects=[self.name])

	@frappe.whitelist()
	def remove_guest(self, email):
		name = frappe.db.get_value("GP Guest Access", {"project": self.name, "user": email})
		if name:
			frappe.delete_doc("GP Guest Access", name)

	@frappe.whitelist()
	def track_visit(self):
		if frappe.flags.read_only:
			return

		values = {"user": frappe.session.user, "project": self.name}
		existing = frappe.db.get_value("GP Project Visit", values)
		if existing:
			visit = frappe.get_doc("GP Project Visit", existing)
			visit.last_visit = frappe.utils.now()
			visit.save(ignore_permissions=True)
		else:
			visit = frappe.get_doc(doctype="GP Project Visit")
			visit.update(values)
			visit.last_visit = frappe.utils.now()
			visit.insert(ignore_permissions=True)

	@property
	def is_followed(self):
		return bool(
			frappe.db.exists("GP Followed Project", {"project": self.name, "user": frappe.session.user})
		)

	@frappe.whitelist()
	def follow(self):
		if not self.is_followed:
			frappe.get_doc(doctype="GP Followed Project", project=self.name).insert(ignore_permissions=True)

	@frappe.whitelist()
	def unfollow(self):
		follow_id = frappe.db.get_value(
			"GP Followed Project", {"project": self.name, "user": frappe.session.user}
		)
		frappe.delete_doc("GP Followed Project", follow_id)


def get_meta_tags(url):
	response = requests.get(url, timeout=2, allow_redirects=True)
	soup = BeautifulSoup(response.text, "html.parser")
	title = soup.find("title").text.strip()

	image = None
	favicon = soup.find("link", rel="icon")
	if favicon:
		image = favicon["href"]

	if image and image.startswith("/"):
		image = urljoin(url, image)

	return {"title": title, "image": image}
