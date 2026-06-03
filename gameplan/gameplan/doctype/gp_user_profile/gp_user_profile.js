// Copyright (c) 2022, Frappe Technologies Pvt Ltd and contributors
// For license information, please see license.txt

const REPORTEE_USER_QUERY =
  "gameplan.gameplan.doctype.gp_user_profile.gp_user_profile.reportee_user_query";

frappe.ui.form.on("GP User Profile", {
  refresh: function (frm) {
    frm.set_query("user", "reportees", () => {
      return { query: REPORTEE_USER_QUERY };
    });
  },
});
