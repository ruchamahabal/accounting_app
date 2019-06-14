# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, accounts
from frappe import _
from frappe.model.document import Document

class JournalEntry(Document):

	def validate(self):
		self.validate_party_for_accounts_receivable()
		self.validate_total_debit_and_credit()
		self.set_against_account()

	def validate_total_debit_and_credit(self):
		for d in self.get("accounting_entries"):
			if d.credit and d.debit:
				frappe.throw(_("You cannot debit and credit same account at the same time"))

		if self.debit_credit_diff:
			frappe.throw(_("Total Debit must be equal to Total Credit. Difference is {0}").format(self.debit_credit_diff))

	def validate_party_for_accounts_receivable(self):
		for d in self.get("accounting_entries"):
			parent_account = frappe.db.get_value("Account", d.account, "parent_account")
			if parent_account == "Accounts Receivable":
				if not d.party:
					frappe.throw(_("Party must be specified for Accounts Receivable type {0}").format(d.account))

	def set_against_account(self):
		accounts_debited = []
		accounts_credited = []
		for e in self.get("accounting_entries"):
			if e.debit>0: accounts_debited.append(e.account)
			if e.credit>0: accounts_credited.append(e.account)

		for e in self.get("accounting_entries"):
			if e.debit>0: e.against_account = ', '.join(list(accounts_credited))
			if e.credit>0: e.against_account = ', '.join(list(accounts_debited))

	def on_submit(self):
		self.update_account_balances()
		self.make_general_ledger_entries()

	def update_account_balances(self):
		accounting_entries = []
		for d in self.get("accounting_entries"):
			accounting_entries.append(d)
		for d in accounting_entries:
			doc = frappe.get_doc("Account", d.account)
			if doc.root_type == 'Asset' or doc.root_type == 'Expense':
				if d.debit > 0:
					doc.balance += d.debit
				elif d.credit > 0:
					doc.balance -= d.credit
			elif doc.root_type == 'Liability' or doc.root_type == 'Income':
				if d.debit > 0:
					doc.balance -= d.debit
				elif d.credit > 0:
					doc.balance += d.credit
			doc.save()

	def make_general_ledger_entries(self):
		from accounts.accounts.general_ledger import make_general_ledger_entries
		gl = []
		for entry in self.get("accounting_entries"):
			if entry.party:
				party = entry.party
				party_type = frappe.db.get_value("Party", entry.party, "party_type")
			else:
				party =''
				party_type = ''
			gl.append({
				'posting_date': self.get("posting_date"),
				'account': entry.account,
				'debit': entry.debit,
				'credit': entry.credit,
				'balance': frappe.db.get_value("Account", entry.account, "balance"),
				'transaction_type': 'Journal Entry',
				'transaction_id': self.get("name"),
				'against_account': entry.against_account,
				'party': party,
				'party_type': party_type
			})
		if gl:
			make_general_ledger_entries(gl)
