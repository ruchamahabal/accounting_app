
from __future__ import unicode_literals
import frappe, accounts
from frappe import _
from frappe.model.document import Document

def make_general_ledger_entries(gl):
    for entry in gl:
        entry.update({"doctype": "GL Entry"})
        gle = frappe.get_doc(entry)
        gle.insert()
