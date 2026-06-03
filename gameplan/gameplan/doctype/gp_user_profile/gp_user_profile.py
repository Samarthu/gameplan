# Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

from time import sleep

import frappe
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists
from frappe.query_builder.functions import Count
from frappe.website.utils import cleanup_page_name
from rq.job import JobStatus

import gameplan
from gameplan.extends.client import check_permissions


class GPUserProfile(Document):
	def autoname(self):
		self.name = self.generate_name()

	def generate_name(self):
		full_name = frappe.db.get_value("User", self.user, "full_name")
		return append_number_if_name_exists(self.doctype, cleanup_page_name(full_name))

	def before_save(self):
		self._resolve_employee()

	def _resolve_employee(self):
		# Auto-link the Employee for this profile's user when not set manually.
		if self.employee or not self.user:
			return
		employee = frappe.db.get_value("Employee", {"user_id": self.user}, "name")
		if employee:
			self.employee = employee

	def on_update(self):
		self._sync_reporting_relationship()

	def on_trash(self):
		# Detach this profile from its manager's reportees on delete.
		if self.reports_to:
			_remove_reportee(self.reports_to, self.user)

	def _sync_reporting_relationship(self):
		before = self.get_doc_before_save()
		old_reports_to = before.reports_to if before else None
		new_reports_to = self.reports_to

		if old_reports_to == new_reports_to:
			return

		if old_reports_to:
			_remove_reportee(old_reports_to, self.user)
		if new_reports_to and new_reports_to != self.name:
			_add_reportee(new_reports_to, self.user)

	@frappe.whitelist()
	def set_image(self, image):
		self.image = image
		self.is_image_background_removed = False
		self.image_background_color = None
		self.original_image = None
		self.save()
		gameplan.refetch_resource("Users")

	@frappe.whitelist()
	def remove_image_background(self, default_color=None):
		from gameplan.gameplan.doctype.gp_user_profile.profile_photo import is_rembg_available

		if not is_rembg_available():
			frappe.throw("Background removal feature is not available. Please install the rembg package.")

		if not self.image:
			frappe.throw("Profile image not found")

		job_id = f"remove-img-bg-{self.name}"
		job = frappe.enqueue(
			remove_imgbg_in_background,
			profile_name=self.name,
			default_color=default_color,
			at_front=True,
			job_id=job_id,
		)
		while True:
			status = job.get_status()
			if status in (JobStatus.QUEUED, JobStatus.STARTED, JobStatus.SCHEDULED):
				print("Waiting for job to complete:", job_id, status)
				sleep(1)
			elif status in (JobStatus.FINISHED, JobStatus.FAILED, JobStatus.CANCELED):
				print("Job status:", job_id, status)
				self.reload()
				break

	@frappe.whitelist()
	def revert_image_background(self):
		if self.original_image:
			self.image = self.original_image
			self.original_image = None
			self.is_image_background_removed = False
			self.image_background_color = None
			self.save()
			gameplan.refetch_resource("Users")

	@frappe.whitelist()
	def is_background_removal_available(self):
		from gameplan.gameplan.doctype.gp_user_profile.profile_photo import is_rembg_available

		return is_rembg_available()

	@frappe.whitelist()
	def sync_from_employee(self):
		"""Pull reporting details from the linked Employee record."""
		employee = frappe.db.get_value("Employee", {"user_id": self.user}, "name") or self.employee
		if not employee:
			frappe.throw("No Employee record found for this user.")

		employee_doc = frappe.db.get_value("Employee", employee, ["name", "reports_to"], as_dict=True)
		if not employee_doc:
			frappe.throw("Employee record not found.")

		self.employee = employee_doc.name
		self.reports_to = _get_gp_profile_for_employee(employee_doc.reports_to) if employee_doc.reports_to else None
		self.reportees = []

		reportee_profiles, skipped_reportees = _get_direct_reportee_profiles(employee_doc.name)
		for profile in reportee_profiles:
			self.append("reportees", {"user": profile.user, "employee": profile.employee})

		self.is_lead = 1 if self.reportees else 0
		self.save()

		return {
			"employee": self.employee,
			"reports_to": self.reports_to,
			"reportees": len(self.reportees),
			"skipped_reportees": len(skipped_reportees),
		}


def create_user_profile(doc, method=None):
	if not frappe.db.exists("GP User Profile", {"user": doc.name}):
		frappe.get_doc(doctype="GP User Profile", user=doc.name).insert(ignore_permissions=True)
		frappe.db.commit()


def delete_user_profile(doc, method=None):
	exists = frappe.db.exists("GP User Profile", {"user": doc.name})
	if exists:
		return frappe.get_doc("GP User Profile", {"user": doc.name}).delete()


def on_user_update(doc, method=None):
	create_user_profile(doc)
	if any(doc.has_value_changed(field) for field in ["full_name", "enabled"]):
		profile = frappe.get_doc("GP User Profile", {"user": doc.name})
		profile.enabled = doc.enabled
		profile.full_name = doc.full_name
		profile.save(ignore_permissions=True)


@frappe.whitelist()
def sync_all_from_employee():
	profiles = frappe.get_all("GP User Profile", pluck="name")
	synced = 0
	skipped = []

	for profile_name in profiles:
		profile = frappe.get_doc("GP User Profile", profile_name)
		try:
			profile.sync_from_employee()
			synced += 1
		except Exception:
			skipped.append(profile_name)
			frappe.log_error(frappe.get_traceback(), f"GP User Profile Employee Sync Failed: {profile_name}")

	return {
		"synced": synced,
		"skipped": len(skipped),
		"skipped_profiles": skipped,
		"total": len(profiles),
	}


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
	doctype = "GP User Profile"
	check_permissions(doctype, parent)
	query = frappe.qb.get_query(
		table=doctype,
		fields=fields,
		filters=filters,
		order_by=order_by,
		offset=start,
		limit=limit,
		group_by=group_by,
	)
	data = query.run(as_dict=True, debug=debug)
	users = [d.user for d in data]

	Discussion = frappe.qb.DocType("GP Discussion")
	discussions_count = (
		frappe.qb.from_(Discussion)
		.select(Count(Discussion.name).as_("count"), Discussion.owner)
		.where(Discussion.owner.isin(users))
		.groupby(Discussion.owner)
	).run(as_dict=True)
	discussions_by_user = {d.owner: d.count for d in discussions_count}

	Comment = frappe.qb.DocType("GP Comment")
	comments_count = (
		frappe.qb.from_(Comment)
		.select(Count(Comment.name).as_("count"), Comment.owner)
		.where(Comment.owner.isin(users) & Comment.deleted_at.isnull())
		.groupby(Comment.owner)
	).run(as_dict=True)
	comments_by_user = {d.owner: d.count for d in comments_count}

	for user in data:
		user.discussions_count = discussions_by_user.get(user.user, 0)
		user.comments_count = comments_by_user.get(user.user, 0)

	return data


def _add_reportee(manager_profile, user):
	"""Add ``user`` to the manager profile's reportees and mark it as a lead."""
	if not user or not frappe.db.exists("GP User Profile", manager_profile):
		return
	manager = frappe.get_doc("GP User Profile", manager_profile)
	if not any(row.user == user for row in manager.reportees):
		manager.append("reportees", {"user": user, "employee": _get_employee_for_user(user)})
	manager.is_lead = 1
	manager.save(ignore_permissions=True)


def _remove_reportee(manager_profile, user):
	"""Remove ``user`` from the manager profile's reportees; clear lead if none left."""
	if not frappe.db.exists("GP User Profile", manager_profile):
		return
	manager = frappe.get_doc("GP User Profile", manager_profile)
	remaining = [row for row in manager.reportees if row.user != user]
	if len(remaining) == len(manager.reportees):
		return
	manager.reportees = remaining
	for idx, row in enumerate(manager.reportees, start=1):
		row.idx = idx
	if not manager.reportees:
		manager.is_lead = 0
	manager.save(ignore_permissions=True)


def _get_gp_profile_for_employee(employee):
	if not employee:
		return None
	user = frappe.db.get_value("Employee", employee, "user_id")
	if not user:
		return None
	return frappe.db.get_value("GP User Profile", {"user": user}, "name")


def _get_direct_reportee_profiles(employee):
	reportees = frappe.db.get_all(
		"Employee",
		filters={"reports_to": employee},
		fields=["name", "user_id"],
	)
	profiles = []
	skipped_employees = []

	for reportee in reportees:
		if not reportee.user_id:
			skipped_employees.append(reportee.name)
			continue

		profile = frappe.db.get_value(
			"GP User Profile",
			{"user": reportee.user_id},
			["name", "user", "employee"],
			as_dict=True,
		)
		if profile:
			profile.employee = profile.employee or reportee.name
			profiles.append(profile)
		else:
			skipped_employees.append(reportee.name)

	return profiles, skipped_employees


def _get_employee_for_user(user):
	if not user:
		return None
	return frappe.db.get_value("Employee", {"user_id": user}, "name")


REPORTEE_ALLOWED_ROLES = (
	"Gameplan Admin",
	"Gameplan Guest",
	"Gameplan Member",
	"General Manager",
)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def reportee_user_query(doctype, txt, searchfield, start, page_len, filters):
	"""Link query: only Users holding one of the allowed Gameplan/GM roles."""
	user = frappe.qb.DocType("User")
	has_role = frappe.qb.DocType("Has Role")
	return (
		frappe.qb.from_(user)
		.inner_join(has_role)
		.on(has_role.parent == user.name)
		.select(user.name, user.full_name)
		.distinct()
		.where(
			(has_role.role.isin(REPORTEE_ALLOWED_ROLES))
			& (user.enabled == 1)
			& ((user.name.like(f"%{txt}%")) | (user.full_name.like(f"%{txt}%")))
		)
		.orderby(user.full_name)
		.limit(page_len)
		.offset(start)
	).run()


def remove_imgbg_in_background(profile_name, default_color=None):
	from gameplan.gameplan.doctype.gp_user_profile.profile_photo import remove_background

	profile = frappe.get_doc("GP User Profile", profile_name)
	file = frappe.get_doc("File", {"file_url": profile.image})
	profile.original_image = file.file_url
	image_content = remove_background(file)
	filename, extn = file.get_extension()
	output_filename = f"{filename}_no_bg.png"
	new_file = frappe.get_doc(
		doctype="File",
		file_name=output_filename,
		content=image_content,
		is_private=0,
		attached_to_doctype=profile.doctype,
		attached_to_name=profile.name,
	).insert()
	profile.image = new_file.file_url
	profile.is_image_background_removed = True
	profile.image_background_color = default_color
	profile.save()
	gameplan.refetch_resource("Users", user=profile.user)
