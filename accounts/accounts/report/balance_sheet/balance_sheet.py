# Copyright (c) 2013, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import functools
from six import itervalues
from frappe.utils import (flt, cint, getdate, get_first_day, add_months, add_days, formatdate)
from frappe import _

value_fields = ("accounts", "fiscal_year")

def execute(filters=None):
	if not filters:
		return [], []
	asset = get_data("Asset", filters.fiscal_year)
	print(asset)
	liability = get_data("Liability", filters.fiscal_year)
	data = []
	data.extend(asset)
	data.extend(liability)
	columns = get_columns(filters.fiscal_year)
	return columns,data

def get_data(root_type, filter_fiscal_year):
	accounts = get_accounts(root_type)
	fiscal_year = frappe.db.sql("""select year_start_date, year_end_date from `tabFiscal Year` where name = %(filter)s""", {'filter': filter_fiscal_year}, as_dict = True)
	year_start_date = fiscal_year[0].get("year_start_date")
	year_end_date = fiscal_year[0].get("year_end_date")
	parent_children_map = {}
	accounts_by_name = {}
	for d in accounts:
		accounts_by_name[d.name] = d
		parent_children_map.setdefault(d.parent_account or None, []).append(d)
	filtered_accounts = []
	def add_to_list(parent, level):
		if level < 10:
			children = parent_children_map.get(parent) or []
			for child in children:
				child.indent = level
				filtered_accounts.append(child)
				add_to_list(child, level + 1)
	add_to_list(None, 0)

	""" fetching gl entries by account """
	gl_entries_by_account = {}
	gl_filters = {
		"from_date": year_start_date,
		"to_date": year_end_date
	}
	for root in frappe.db.sql("""select lft, rgt from tabAccount where root_type = %s""", root_type, as_dict = 1):
		child_accounts = frappe.db.sql_list("""select name from tabAccount where lft >= %s and rgt <= %s""", (root.lft, root.rgt))
		additional_condition = " where account in ({})".format(", ".join([frappe.db.escape(d) for d in child_accounts]))
		gl_entries = frappe.db.sql("""select posting_date, account, debit, credit, balance from `tabGL Entry`{additional_conditions} and posting_date < %(to_date)s order by account, posting_date""".format(additional_conditions = additional_condition), gl_filters, as_dict = True)

		for entry in gl_entries:
			gl_entries_by_account.setdefault(entry.account, []).append(entry)

	"""calculate balances for each account based on gl entries"""
	for entries in itervalues(gl_entries_by_account):
		for entry in entries:
			d = accounts_by_name.get(entry.account)
			if entry.posting_date <= year_end_date and entry.posting_date >= year_start_date:
				d[filter_fiscal_year] = d.get(filter_fiscal_year, 0.0) + flt(entry.get("debit")) - flt(entry.get("credit"))
			if entry.posting_date < year_start_date:
				d["opening_balance"] = d.get("opening_balance", 0.0) + flt(entry.get("debit")) - flt(entry.get("credit"))

	"""accumulate child account values into parent accounts"""
	for d in reversed(filtered_accounts):
		if d.parent_account:
			accounts_by_name[d.parent_account][fiscal_year] = accounts_by_name[d.parent_account].get(fiscal_year, 0.0) + d.get(fiscal_year, 0.0)
		# accounts_by_name[d.parent_account]["opening_balance"] = accounts_by_name[d.parent_account].get(opening_balance, 0.0) + d.get(opening_balance, 0.0)

	"""prepare data"""
	data = []
	print(filtered_accounts)
	for d in filtered_accounts:

		# add to output
		row = frappe._dict({
			"account": _(d.name),
			"parent_account": _(d.parent_account) if d.parent_account else '',
			"indent": flt(d.indent),
			"year_start_date": year_start_date,
			"year_end_date": year_end_date,
			"is_group": d.is_group,
			"opening_balance": d.get("opening_balance", 0.0) * (1 if root_type=="Asset" else -1),
			"account_name": ('%s - %s' %(_(d.account_number), _(d.account_name))
				if d.account_number else _(d.account_name))
		})

		if root_type=="Liability":
				# change sign based on Debit or Credit, since calculation is done using (debit - credit)
				d[filter_fiscal_year] *= -1
		total += flt(row[filter_fiscal_year])
		row["total"] = total
		data.append(row)
	return data

def get_accounts(root_type):
	return frappe.db.sql("""select name, account_number, parent_account, lft, rgt, root_type, account_name, is_group, lft, rgt
		from `tabAccount`
		where root_type=%s order by lft""", (root_type), as_dict=True)

def get_columns(fiscal_year):
	columns = [{
		"fieldname": "account",
		"label": _("Account"),
		"fieldtype": "Link",
		"options": "Account",
		"width": 300
	},
	{
		"fieldname": fiscal_year,
		"label": fiscal_year,
		"fieldtype": "Currency"
	}]
	return columns
