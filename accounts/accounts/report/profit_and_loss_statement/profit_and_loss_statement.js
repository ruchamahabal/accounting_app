// Copyright (c) 2016, Frappe and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Profit and Loss Statement"] = {
	"filters": [
		{
			"fieldname":"from_fiscal_year",
			"label": __("Start date"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd": 1
		},
		{
			"fieldname": "to_fiscal_year",
			"label": __("End date"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd": 1
		}

	]
};
