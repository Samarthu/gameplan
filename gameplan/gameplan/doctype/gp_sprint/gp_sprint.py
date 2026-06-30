import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class GPSprint(Document):
	def before_insert(self):
		if not self.title:
			self.title = self._generate_title()

	def on_trash(self):
		count = frappe.db.count("GP Task", {"sprint": self.name})
		if count:
			frappe.throw(
				frappe._("Delete the {0} task(s) in this sprint before deleting it.").format(count)
			)

	def _generate_title(self):
		if self.start_date and self.end_date:
			s = getdate(self.start_date)
			e = getdate(self.end_date)
			if s.month == e.month:
				return f"Sprint - {s.strftime('%b')} {s.day}–{e.day}"
			return f"Sprint - {s.strftime('%b')} {s.day} – {e.strftime('%b')} {e.day}"
		elif self.start_date:
			s = getdate(self.start_date)
			return f"Sprint - {s.strftime('%b')} {s.day}"
		return "Sprint - 1"


@frappe.whitelist()
def get_sprint_task_counts(team):
	rows = frappe.db.get_all(
		"GP Task",
		filters={"team": team, "sprint": ["is", "set"]},
		fields=["sprint", "count(*) as count"],
		group_by="sprint",
	)
	return {r.sprint: r.count for r in rows}
