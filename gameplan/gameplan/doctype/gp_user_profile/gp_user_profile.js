// Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
// For license information, please see license.txt

const REPORTEE_USER_QUERY =
  "gameplan.gameplan.doctype.gp_user_profile.gp_user_profile.reportee_user_query";

frappe.ui.form.on("GP User Profile", {
  refresh: function (frm) {
    frm.add_custom_button(__("Sync From Employee"), () => {
      if (frm.is_new()) {
        frappe.msgprint(__("Please save this GP User Profile before syncing."));
        return;
      }

      frm.call("sync_from_employee").then((response) => {
        const result = response.message || {};
        frm.reload_doc();
        frappe.show_alert({
          message: __(
            "Synced from Employee. {0} reportee(s) updated.",
            [result.reportees || 0]
          ),
          indicator: "green",
        });
      });
    });

    frm.set_query("user", "reportees", () => {
      return { query: REPORTEE_USER_QUERY };
    });
    frm.set_query("employee", () => {
      return {
        filters: {
          user_id: frm.doc.user,
        },
      };
    });
  },
});
