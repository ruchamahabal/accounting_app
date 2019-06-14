// Copyright (c) 2019, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fiscal Year', {
	onload: function(frm) {
      frm.set_value("year_start_date", frappe.datetime.add_days(frappe.defaults.get_default("year_end_date"), 1))
	},
  year_start_date: function(frm) {
		var year_end_date = frappe.datetime.add_days(frappe.datetime.add_months(frm.doc.year_start_date, 12), -1);
		frm.set_value("year_end_date", year_end_date);
	},
});
