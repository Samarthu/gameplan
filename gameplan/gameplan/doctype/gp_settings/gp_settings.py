# Copyright (c) 2026, Frappe Technologies Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class GPSettings(Document):
	def validate(self):
		n = frappe.utils.cint(self.max_goals_per_project or 3)
		if n < 1:
			frappe.throw(_("Maximum Goals Per Project must be at least 1."))
		self.max_goals_per_project = n

