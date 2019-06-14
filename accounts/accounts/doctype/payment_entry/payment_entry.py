# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PaymentEntry(Document):
	def on_submit(self):
		self.update_account_balances()
		self.make_general_ledger_entries()

	def update_account_balances(self):
		doc_paid_from = frappe.get_doc("Account", self.get("account_paid_from"))
		doc_paid_to = frappe.get_doc("Account", self.get("account_paid_to"))
		doc_paid_from.balance -= self.get("amount_paid")
		doc_paid_from.save()
		doc_paid_to.balance += self.get("amount_paid")
		doc_paid_to.save()

	def make_general_ledger_entries(self):
		from accounts.accounts.general_ledger import make_general_ledger_entries
		gl = []
		gl.append({
			'posting_date': self.get('posting_date'),
			'account': self.get('account_paid_from'),
			'debit': 0.00,
			'credit': self.get('amount_paid'),
			'balance': frappe.db.get_value('Account', self.get('account_paid_from'), 'balance'),
			'transaction_type': 'Payment Entry',
			'transaction_id': self.get('name'),
			'against_account': self.get('account_paid_to'),
			'party': self.get('party'),
			'party_type': self.get('party_type')
		})
		gl.append({
			'posting_date': self.get('posting_date'),
			'account': self.get('account_paid_to'),
			'debit': self.get('amount_paid'),
			'credit': 0.00,
			'balance': frappe.db.get_value('Account', self.get('account_paid_to'), 'balance'),
			'transaction_type': 'Payment Entry',
			'transaction_id': self.get('name'),
			'against_account': self.get("account_paid_from"),
			'party': '',
			'party_type': ''
		})
		make_general_ledger_entries(gl)
