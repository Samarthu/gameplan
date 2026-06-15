import frappe

__version__ = "0.0.1"


def is_guest():
	if frappe.session.user == "Administrator":
		return False
	roles = frappe.get_roles()
	if "Gameplan Member" in roles or "Gameplan Admin" in roles:
		return False
	return "Gameplan Guest" in roles


def refetch_resource(cache_key: str | list, user=None):
	frappe.publish_realtime(
		"refetch_resource", {"cache_key": cache_key}, user=user or frappe.session.user, after_commit=True
	)


def notify_project_merged(source_key: str, target_key: str, team: str | None = None) -> None:
	"""Refresh Gameplan UI after a project merge (bulk SQL updates skip doc realtime)."""
	payload = {"source": source_key, "target": target_key, "team": team}
	frappe.publish_realtime("project_merged", payload, after_commit=True)
	refetch_resource("Projects")
	refetch_resource("Linked Projects")
