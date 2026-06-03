frappe.listview_settings["GP User Profile"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Sync All From Employee"), () => {
			frappe.confirm(
				__("This will sync reporting details for all GP User Profiles from Employee records. Continue?"),
				() => {
					frappe.call({
						method:
							"gameplan.gameplan.doctype.gp_user_profile.gp_user_profile.sync_all_from_employee",
						freeze: true,
						freeze_message: __("Syncing GP User Profiles from Employee records..."),
						callback(response) {
							const result = response.message || {};
							listview.refresh();
							frappe.show_alert({
								message: __(
									"Synced {0} of {1} GP User Profile(s). {2} skipped.",
									[result.synced || 0, result.total || 0, result.skipped || 0]
								),
								indicator: result.skipped ? "orange" : "green",
							});
						},
					});
				}
			);
		});
	},
};
