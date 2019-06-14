# Copyright (c) 2013, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import functools
from six import itervalues
from frappe.utils import (flt, cint, getdate, get_first_day, add_months, add_days, formatdate)
from frappe import _

def execute(filters=None):
	if not filters:
		return [], []
	fiscal_year = get_fiscal_year_dates(filters.fiscal_year)
	asset = get_data("Asset", fiscal_year)
	liability = get_data("Liability", fiscal_year)
	data = []
	data.extend(asset)
	data.extend(liability)
	print(asset)
	columns = get_columns(filters.fiscal_year)

	return columns,data

def get_fiscal_year_dates(filter):
	fiscal_year = frappe.db.sql("""select year_start_date, year_end_date from `tabFiscal Year` where name = %(filter)s""", {'filter': filter}, as_dict = 1)
	return fiscal_year

def get_data(root_type, fiscal_year):
	accounts = get_accounts(root_type)
	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)
	# print(accounts)
	# print(accounts_by_name)
	print(parent_children_map)

	gl_entries_by_account = {}
	for root in frappe.db.sql("""select lft, rgt from `tabAccount` where root_type=%(root_type)s""", {'root_type': root_type}, as_dict=1):

		set_gl_entries_by_account(
			fiscal_year[0].get('year_start_date'),
			fiscal_year[0].get('year_end_date'),
			root.lft, root.rgt,
			gl_entries_by_account
		)
	print(gl_entries_by_account)
	# calculate_values(accounts_by_name, gl_entries_by_account, fiscal_year)
	accumulate_values_into_parents(accounts, accounts_by_name, fiscal_year)
	out = prepare_data(accounts, fiscal_year)
	return out


def get_accounts(root_type):
	return frappe.db.sql("""select name, account_number, parent_account, lft, rgt, root_type, account_name, is_group, lft, rgt
		from `tabAccount`
		where root_type=%s order by lft""", (root_type), as_dict=True)

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
	"""Sort root types as Asset, Liability"""
	def compare_accounts(a, b):
		if is_root:
			if a.root_type != b.root_type and a.root_type == "Asset":
				return -1
		else:
			# sort by key (number) or name
			return cmp(a[key], b[key])
		return 1
	accounts.sort(key = functools.cmp_to_key(compare_accounts))

def set_gl_entries_by_account(from_date, to_date, root_lft, root_rgt, gl_entries_by_account):
	"""Returns a dict like { "account": [gl entries], ... }"""
	accounts = frappe.db.sql_list("""select name from `tabAccount` where lft >= %s and rgt <= %s""", (root_lft, root_rgt))
	conditions = "account in ({})".format(", ".join([frappe.db.escape(d) for d in accounts]))

	gl_filters = {
		"from_date": from_date,
		"to_date": to_date,
	}

	gl_entries = frappe.db.sql("""select posting_date, account, debit, credit, balance from `tabGL Entry` where {conditions} and posting_date <= %(to_date)s order by account, posting_date""".format(conditions=conditions), gl_filters, as_dict=True)

	for entry in gl_entries:
		gl_entries_by_account.setdefault(entry.account, []).append(entry)

	return gl_entries_by_account

def calculate_values(accounts_by_name, gl_entries_by_account, fiscal_year):
	for entries in itervalues(gl_entries_by_account):
		for entry in entries:
			d = accounts_by_name.get(entry.account)
			if not d:
				frappe.msgprint(
					_("Could not retrieve information for {0}.".format(entry.account)), title="Error",
					raise_exception=1
				)
			# # check if posting date is within the period
			# if entry.posting_date <= fiscal_year.year_end_date:
			# 	if entry.posting_date >= fiscal_year.year_start_date):
			# 		d[period.key] = d.get(period.key, 0.0) + flt(entry.debit) - flt(entry.credit)

			if entry.posting_date < fiscal_year[0].get('year_start_date'):
				d["balance"] = d.get("balance", 0.0) + flt(entry.debit) - flt(entry.credit)

def accumulate_values_into_parents(accounts, accounts_by_name, fiscal_year):
	"""accumulate children's values in parent accounts"""
	for d in reversed(accounts):
		if d.parent_account:
			accounts_by_name[d.parent_account]["balance"] = accounts_by_name[d.parent_account].get("balance",0.0) + d.get("balance", 0.0)

def prepare_data(accounts, fiscal_year):
	data = []
	year_start_date = fiscal_year[0].get('year_start_date').strftime("%Y-%m-%d")
	year_end_date = fiscal_year[0].get('year_end_date').strftime("%Y-%m-%d")
	for d in accounts:
		# add to output
		has_value = False
		total = 0
		row = frappe._dict({
			"account": _(d.name),
			"parent_account": _(d.parent_account) if d.parent_account else '',
			"indent": flt(d.indent),
			"year_start_date": year_start_date,
			"year_end_date": year_end_date,
			"is_group": d.is_group,
			"balance": d.get("balance", 0.0),
			"account_name": ('%s - %s' %(_(d.account_number), _(d.account_name))
				if d.account_number else _(d.account_name))
		})
		print("======="+row)
		# for period in period_list:
		# 	if d.get(period.key) and balance_must_be == "Credit":
		# 		# change sign based on Debit or Credit, since calculation is done using (debit - credit)
		# 		d[period.key] *= -1
		#
		# 	row[period.key] = flt(d.get(period.key, 0.0), 3)
		#
		# 	if abs(row[period.key]) >= 0.005:
		# 		# ignore zero values
		# 		has_value = True
		# 		total += flt(row[period.key])
		#
		# row["has_value"] = has_value
		# row["total"] = total
		data.append(row)
	print(data)
	return data

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
	}
	]
	return columns
