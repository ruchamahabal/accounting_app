# Copyright (c) 2013, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _ , _dict
from frappe.utils import getdate, flt

def execute(filters=None):
	if not filters:
		return [], []
	account_details = {}
	for acc in frappe.db.sql("""select name, is_group from tabAccount""", as_dict=1):
		account_details.setdefault(acc.name, acc)
	print(account_details)
	validate_filters(filters, account_details)
	columns = get_columns(filters)
	data = get_data(filters, account_details)
	return columns, data

def validate_filters(filters, account_details):
	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

	if filters.get("account") and not account_details.get(filters.account):
		frappe.throw(_("Account {0} does not exists").format(filters.account))

def get_data(filters, account_details):
	gl_entries = get_gl_entries(filters)
	data = get_data_with_opening_closing(filters, account_details, gl_entries)
	result = get_result_as_list(data, filters)
	return result

def get_gl_entries(filters):
	select_fields = """, debit, credit """
	order_by_statement = "order by posting_date, account"
	gl_entries = frappe.db.sql(
		"""
		select * from `tabGL Entry` {conditions} {order_by_statement}"""
		.format(
			conditions=get_conditions(filters),
			order_by_statement=order_by_statement
		),
		filters, as_dict=1)
	return gl_entries

def get_conditions(filters):
	conditions = []
	if filters.get("account"):
		lft, rgt = frappe.db.get_value("Account", filters["account"], ["lft", "rgt"])
		conditions.append("""account in (select name from tabAccount
			where lft>=%s and rgt<=%s and docstatus<2)""" % (lft, rgt))
	if not (filters.get("account")):
		conditions.append("posting_date >=%(from_date)s")
		conditions.append("posting_date <=%(to_date)s")
	from frappe.desk.reportview import build_match_conditions
	match_conditions = build_match_conditions("GL Entry")
	if match_conditions:
		conditions.append(match_conditions)
	return "where {}".format(" and ".join(conditions)) if conditions else ""

def get_result_as_list(data, filters):
	for d in data:
		d['against'] = d.get('against_account')
		if not d.get('posting_date'):
			balance = 0
		balance = get_balance(d, balance, 'debit', 'credit')
		d['balance'] = balance
	return data

def get_balance(row, balance, debit_field, credit_field):
	balance += (row.get(debit_field, 0) -  row.get(credit_field, 0))
	return balance

def get_data_with_opening_closing(filters, account_details, gl_entries):
	data = []
	gle_map = frappe._dict()
	totals, entries = get_accountwise_gle(filters, gl_entries, gle_map)
	#table starts with opening, then the entries, total and then closing
	data.append(totals.opening)
	data += entries
	data.append(totals.total)
	data.append(totals.closing)
	return data

def get_totals_dict():
	def _get_debit_credit_dict(label):
		return _dict(
			account="'{0}'".format(label),
			debit=0.0,
			credit=0.0
		)
	return _dict(
		opening = _get_debit_credit_dict(_('Opening')),
		total = _get_debit_credit_dict(_('Total')),
		closing = _get_debit_credit_dict(_('Closing (Opening + Total)'))
	)

def get_accountwise_gle(filters, gl_entries, gle_map):
	totals = get_totals_dict()
	entries = []

	def update_value_in_dict(data, key, gle):
		data[key].debit += flt(gle.debit)
		data[key].credit += flt(gle.credit)

	from_date, to_date = getdate(filters.from_date), getdate(filters.to_date)
	for gle in gl_entries:
		if (gle.posting_date < from_date):
			update_value_in_dict(totals, 'opening', gle)
			update_value_in_dict(totals, 'closing', gle)

		elif gle.posting_date <= to_date:
			update_value_in_dict(totals, 'total', gle)
			entries.append(gle)
			update_value_in_dict(totals, 'closing', gle)

	return totals, entries

def get_columns(filters):
	columns = [
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 90
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180
		},
		{
			"label": _("Debit ({0})".format('INR')),
			"fieldname": "debit",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Credit ({0})".format('INR')),
			"fieldname": "credit",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Balance ({0})".format('INR')),
			"fieldname": "balance",
			"fieldtype": "Float",
			"width": 130
		}
	]

	columns.extend([
		{
			"label": _("Transaction Type"),
			"fieldname": "transaction_type",
			"width": 120
		},
		{
			"label": _("Transaction Id"),
			"fieldname": "transaction_id",
			"fieldtype": "Dynamic Link",
			"options": "transaction_type",
			"width": 180
		},
		{
			"label": _("Against Account"),
			"fieldname": "against",
			"width": 120
		},
		{
			"label": _("Party Type"),
			"fieldname": "party_type",
			"width": 100
		},
		{
			"label": _("Party"),
			"fieldname": "party",
			"width": 100
		},
	])

	return columns
