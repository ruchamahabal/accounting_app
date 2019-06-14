# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.nestedset import NestedSet
from frappe.model.document import Document

class Account(NestedSet):
	nsm_parent_field = 'parent_account'
