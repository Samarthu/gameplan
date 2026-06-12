# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today

from gameplan.executive_dashboard import (
	_team_accountability,
	can_access_executive_dashboard,
	compute_team_health,
	get_ceo_cockpit_data,
)


class TestExecutiveDashboard(FrappeTestCase):
	def test_compute_team_health_matrix(self):
		thresholds = {
			"red_overdue": 5,
			"amber_overdue_min": 1,
			"amber_overdue_max": 4,
			"stale_task_days": 14,
			"stale_project_days": 14,
			"sprint_min_completion_pct": 70,
		}
		self.assertEqual(
			compute_team_health({"overdue_count": 5, "stale_count": 0, "at_risk_goals": 0}, thresholds),
			"red",
		)
		self.assertEqual(
			compute_team_health({"overdue_count": 0, "at_risk_goals": 1}, thresholds),
			"red",
		)
		self.assertEqual(
			compute_team_health({"overdue_count": 0, "sprint_slip": True}, thresholds),
			"red",
		)
		self.assertEqual(
			compute_team_health({"overdue_count": 2, "stale_count": 0}, thresholds),
			"amber",
		)
		self.assertEqual(
			compute_team_health({"overdue_count": 0, "stale_count": 3}, thresholds),
			"amber",
		)
		self.assertEqual(
			compute_team_health({"overdue_count": 0, "stale_projects": 1}, thresholds),
			"amber",
		)
		self.assertEqual(
			compute_team_health({"overdue_count": 0, "stale_count": 0}, thresholds),
			"green",
		)

	def test_team_accountability_missing_lead(self):
		acc, _msg = _team_accountability(None, "red", {"overdue_count": 10})
		self.assertEqual(acc, "missing_lead")

	def test_team_accountability_underperforming(self):
		acc, msg = _team_accountability("lead@example.com", "red", {"overdue_count": 6, "completed_7d": 0})
		self.assertEqual(acc, "underperforming")
		self.assertIn("6", msg)

	def test_admin_can_access_executive_dashboard(self):
		self.assertTrue(can_access_executive_dashboard("Administrator"))

	def test_integration_red_team_overdue_tasks(self):
		frappe.set_user("Administrator")
		team = frappe.get_doc({"doctype": "GP Team", "title": "Exec Test Team"}).insert()
		project = frappe.get_doc(
			{
				"doctype": "GP Project",
				"title": "Exec Test Project",
				"team": team.name,
				"status": "Open",
			}
		).insert()
		for i in range(5):
			frappe.get_doc(
				{
					"doctype": "GP Task",
					"title": f"Overdue task {i}",
					"team": team.name,
					"project": project.name,
					"status": "Todo",
					"due_date": add_days(today(), -2),
				}
			).insert()

		data = get_ceo_cockpit_data()
		row = next((t for t in data["teams"] if t["name"] == team.name), None)
		self.assertIsNotNone(row)
		self.assertEqual(row["health"], "red")
		self.assertGreaterEqual(row["metrics"]["overdue_count"], 5)
		self.assertIn("summary", data)
		self.assertIn("lead_accountability", data)
		self.assertIn("people", data)
		self.assertIn("management_insights", data)
