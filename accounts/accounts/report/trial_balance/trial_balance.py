# Copyright (c) 2013, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _ , _dict
import functools
from frappe.utils import getdate, flt

value_fields = ("opening_debit", "opening_credit", "debit", "credit", "closing_debit", "closing_credit")

def execute(filters=None):
	validate_filters(filters)
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def validate_filters(filters):
	filters.from_date = getdate(filters.from_date)
	filters.to_date = getdate(filters.to_date)
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

def get_data(filters):
	accounts = frappe.db.sql("""select name, account_number, parent_account, account_name, root_type, lft, rgt
		from `tabAccount` order by lft""", as_dict=True)
	if not accounts:
		return None
	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)

	min_lft, max_rgt = frappe.db.sql("""select min(lft), max(rgt) from `tabAccount`""")[0]
	gl_entries_by_account = {}
	opening_balances = get_opening_balances(filters)
	set_gl_entries_by_account(filters.from_date, filters.to_date, min_lft, max_rgt, filters, gl_entries_by_account)
	total_row = calculate_values(accounts, gl_entries_by_account, opening_balances, filters)
	accumulate_values_into_parents(accounts, accounts_by_name)

	data = prepare_data(accounts, filters, total_row, parent_children_map)
	return data

def filter_accounts(accounts, depth=10):
	parent_children_map = {}
	accounts_by_name = {}
	for d in accounts:
		accounts_by_name[d.name] = d
		parent_children_map.setdefault(d.parent_account or None, []).append(d)
	filtered_accounts = []
	def add_to_list(parent, level):
		if level < depth:
			children = parent_children_map.get(parent) or []
			sort_accounts(children, is_root=True if parent==None else False)
			for child in children:
				child.indent = level
				filtered_accounts.append(child)
				add_to_list(child.name, level + 1)
	add_to_list(None, 0)
	return filtered_accounts, accounts_by_name, parent_children_map

def sort_accounts(accounts, is_root=False, key="name"):
	"""Sort root types as Asset, Liability, Income, Expense"""
	def compare_accounts(a, b):
		if is_root:
			if a.root_type != b.root_type and a.root_type == "Asset":
				return -1
			if a.root_type == "Income" and b.root_type == "Expense":
				return -1
		else:
			# sort by key (number) or name
			return cmp(a[key], b[key])
		return 1
	accounts.sort(key = functools.cmp_to_key(compare_accounts))

def get_opening_balances(filters):
	opening = get_rootwise_opening_balances(filters)
	return opening

def get_rootwise_opening_balances(filters):
	gle = frappe.db.sql("""
		select
			account, sum(debit) as opening_debit, sum(credit) as opening_credit
		from `tabGL Entry`
		where
		   (posting_date < %(from_date)s)
		group by account""",
		{
			"from_date": filters.from_date,
		},
		as_dict=True)
	opening = frappe._dict()
	for d in gle:
		opening.setdefault(d.account, d)
	return opening

def set_gl_entries_by_account(from_date, to_date, root_lft, root_rgt, filters, gl_entries_by_account):
	"""Returns a dict like { "account": [gl entries], ... }"""
	accounts = frappe.db.sql_list("""select name from `tabAccount`
		where lft >= %s and rgt <= %s""", (root_lft, root_rgt))

	gl_filters = {
		"from_date": from_date,
		"to_date": to_date,
	}
	for key, value in filters.items():
		if value:
			gl_filters.update({
				key: value
			})
	gl_entries = frappe.db.sql("""select posting_date, account, debit, credit from `tabGL Entry`
		where account in ({}) and posting_date <= %(to_date)s
		order by account, posting_date""".format(", ".join([frappe.db.escape(d) for d in accounts])), gl_filters, as_dict=True)
	for entry in gl_entries:
		gl_entries_by_account.setdefault(entry.account, []).append(entry)
	return gl_entries_by_account

def calculate_values(accounts, gl_entries_by_account, opening_balances, filters):
	init = {
		"opening_debit": 0.0,
		"opening_credit": 0.0,
		"debit": 0.0,
		"credit": 0.0,
		"closing_debit": 0.0,
		"closing_credit": 0.0
	}

	total_row = {
		"account": "'" + _("Total") + "'",
		"account_name": "'" + _("Total") + "'",
		"warn_if_negative": True,
		"opening_debit": 0.0,
		"opening_credit": 0.0,
		"debit": 0.0,
		"credit": 0.0,
		"closing_debit": 0.0,
		"closing_credit": 0.0,
		"parent_account": None,
		"indent": 0,
		"has_value": True,
	}

	for d in accounts:
		d.update(init.copy())
		# add opening
		d["opening_debit"] = opening_balances.get(d.name, {}).get("opening_debit", 0)
		d["opening_credit"] = opening_balances.get(d.name, {}).get("opening_credit", 0)

		for entry in gl_entries_by_account.get(d.name, []):
			d["debit"] += flt(entry.debit)
			d["credit"] += flt(entry.credit)

		d["closing_debit"] = d["opening_debit"] + d["debit"]
		d["closing_credit"] = d["opening_credit"] + d["credit"]
		total_row["debit"] += d["debit"]
		total_row["credit"] += d["credit"]

		if d["root_type"] == "Asset" or d["root_type"] == "Expense":
			d["opening_debit"] -= d["opening_credit"]
			d["opening_credit"] = 0.0
			total_row["opening_debit"] += d["opening_debit"]
		if d["root_type"] == "Liability" or d["root_type"] == "Income":
			d["opening_credit"] -= d["opening_debit"]
			d["opening_debit"] = 0.0
			total_row["opening_credit"] += d["opening_credit"]
		if d["root_type"] == "Asset" or d["root_type"] == "Expense":
			d["closing_debit"] -= d["closing_credit"]
			d["closing_credit"] = 0.0
			total_row["closing_debit"] += d["closing_debit"]
		if d["root_type"] == "Liability" or d["root_type"] == "Income":
			d["closing_credit"] -= d["closing_debit"]
			d["closing_debit"] = 0.0
			total_row["closing_credit"] += d["closing_credit"]
	return total_row

def accumulate_values_into_parents(accounts, accounts_by_name):
	for d in reversed(accounts):
		if d.parent_account:
			for key in value_fields:
				accounts_by_name[d.parent_account][key] += d[key]

def prepare_data(accounts, filters, total_row, parent_children_map):
	data = []
	for d in accounts:
		has_value = False
		row = {
			"account": d.name,
			"parent_account": d.parent_account,
			"indent": d.indent,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"account_name": ('{} - {}'.format(d.account_number, d.account_name)
				if d.account_number else d.account_name)
		}
		prepare_opening_and_closing(d)

		for key in value_fields:
			row[key] = flt(d.get(key, 0.0), 3)

			if abs(row[key]) >= 0.005:
				# ignore zero values
				has_value = True

		row["has_value"] = has_value
		data.append(row)

	data.extend([{},total_row])

	return data

def prepare_opening_and_closing(d):
	d["closing_debit"] = d["opening_debit"] + d["debit"]
	d["closing_credit"] = d["opening_credit"] + d["credit"]
	if d["root_type"] == "Asset" or d["root_type"] == "Expense":
		d["opening_debit"] -= d["opening_credit"]
		d["opening_credit"] = 0.0
	if d["root_type"] == "Liability" or d["root_type"] == "Income":
		d["opening_credit"] -= d["opening_debit"]
		d["opening_debit"] = 0.0
	if d["root_type"] == "Asset" or d["root_type"] == "Expense":
		d["closing_debit"] -= d["closing_credit"]
		d["closing_credit"] = 0.0
	if d["root_type"] == "Liability" or d["root_type"] == "Income":
		d["closing_credit"] -= d["closing_debit"]
		d["closing_debit"] = 0.0

def get_columns():
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300
		},
		{
			"fieldname": "opening_debit",
			"label": _("Opening (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "opening_credit",
			"label": _("Opening (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_debit",
			"label": _("Closing (Dr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_credit",
			"label": _("Closing (Cr)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		}
	]
