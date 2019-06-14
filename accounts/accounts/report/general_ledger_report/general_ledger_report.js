// Copyright (c) 2016, Frappe and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["General Ledger Report"] = {
	"filters": [
			{
					"fieldname":"account",
					"label": __("Account"),
					"fieldtype": "Link",
					"options": "Account",
					"get_query": function() {
					var company = frappe.query_report.get_filter_value('account');
						return {
							"doctype": "Account",
							"filters": {
								'is_group':0,
							}
						}
					}
			},
			{
					"fieldname":"from_date",
					"label":__("From Date"),
					"fieldtype":"Date",
					"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
					"reqd": 1
			},
			{
					"fieldname":"to_date",
					"label":__("To Date"),
					"fieldtype":"Date",
					"default": frappe.datetime.get_today(),
					"reqd": 1
			},
	]
};
