# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class PurchaseInvoice(Document):
	def validate(self):
		self.validate_item_quantity_not_zero()
		self.validate_due_date()

	def validate_item_quantity_not_zero(self):
		for d in self.get("items"):
			if d.quantity == 0:
				frappe.throw(_("Item quantity cannot be 0"))

	def validate_due_date(self):
		if self.get("due_date_for_payment") < self.get("posting_date"):
			frappe.throw(_("Payment Due Date cannot be before Purchase Invoice Posting Date"))

	def on_submit(self):
		self.update_account_balances()
		self.make_general_ledger_entries()

	def update_account_balances(self):
		doc = frappe.get_doc("Account", self.get("credit_to"))
		doc.balance -= self.get("total_amount")
		doc.save()
		doc = frappe.get_doc("Account", self.get("expense_account"))
		doc.balance += self.get("total_amount")
		doc.save()

	def make_general_ledger_entries(self):
		from accounts.accounts.general_ledger import make_general_ledger_entries
		gl = []
		gl.append({
			'posting_date': self.get('posting_date'),
			'account': self.get('credit_to'),
			'debit': 0.0,
			'credit': self.get('total_amount'),
			'balance': frappe.db.get_value('Account', self.get('credit_to'), 'balance'),
			'transaction_type': 'Purchase Invoice',
			'transaction_id': self.get('name'),
			'against_account': self.get('expense_account'),
			'party': self.get('supplier'),
			'party_type': 'Supplier'
		})
		gl.append({
			'posting_date': self.get('posting_date'),
			'account': self.get('expense_account'),
			'debit': self.get('total_amount'),
			'credit': 0.0,
			'balance': frappe.db.get_value('Account', self.get('expense_account'), 'balance'),
			'transaction_type': 'Purchase Invoice',
			'transaction_id': self.get('name'),
			'against_account': self.get("credit_to"),
			'party': '',
			'party_type': ''
		})
		make_general_ledger_entries(gl)
