# Copyright (c) 2013, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe

def execute(filters=None):
	if not filters:
		return [], []
	period_list = get_period_list(filters.from_fiscal_year, filters.to_fiscal_year)

def get_period_list(from_fiscal_year, to_fiscal_year):
	
