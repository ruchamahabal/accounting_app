from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'transactions': [
			{
				'label': _('Payment'),
				'items': ['Payment Entry', 'Journal Entry']
	        },
		],
		'non_standard_fieldnames': {
			'Payment Entry': 'reference_name',

		}
	}
