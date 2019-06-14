from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Accounting"),
			"icon": "octicon octicon-briefcase",
			"items": [
				{
					"type": "doctype",
					"name": "Account",
					"label": _("Accounts"),
					"description": _("All the accounts")
				},
                {
                    "type": "doctype",
                    "name": "Item",
                    "label": _("Items"),
                    "description": _("Items for sales and purchase")
                },
                {
                    "type": "doctype",
                    "name": "Party",
                    "label": _("Party"),
                    "description": _("A Party can be a Customer or Supplier")
                },
			]
		},
        {
            "label": _("Transactions"),
            "icon": "octicon octicon-briefcase",
            "items": [
                {
                    "type": "doctype",
                    "name": "Journal Entry",
                    "label": _("Journal Entry"),
                    "description":_("Journal Entry keeps a track of all the transactions")
                },
                {
                    "type": "doctype",
                    "name": "Sales Invoice",
                    "label": _("Sales Invoice"),
                    "description": _("Sales Invoice is a bill for the Supplier giving a bill of sales")
                },
                {
                    "type":"doctype",
                    "name": "Purchase Invoice",
                    "label": _("Purchase Invoice"),
                    "description": _("Purchase Invoice is a bill for the Customers who have some purchase")
                }
            ]
        },
        {
            "label": _("Reports"),
            "icon": "octicon octicon-books",
            "items": [
				{
					"type": "report",
					"name": "General Ledger Report",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance",
					"doctype": "GL Entry",
					"is_query_report": True
				},
                {
                    "type": "report",
                    "name": "Balance Sheet",
                    "doctype": "GL Entry",
                    "is_query_report": True
                },
				{
					"type": "report",
					"name": "Profit and Loss Statement",
					"doctype": "GL Entry",
					"is_query_report": True
				}
            ]
        }
	]
