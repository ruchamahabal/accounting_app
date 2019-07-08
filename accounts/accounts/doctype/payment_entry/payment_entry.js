// Copyright (c) 2019, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Entry', {
	refresh: function(frm) {
    if(frm.doc.payment_type == "Receive"){
      frm.set_query('account_paid_to', function(){
          return {
            filters: {
              is_group: 0,
              parent_account: 'Current Assets'
            }
          }
      });
      frm.set_query('account_paid_from', function(){
          return {
            filters:{
              is_group: 0,
              parent_account: 'Accounts Receivable'
            }
          }
      });
  	}

    else if(frm.doc.payment_type == "Pay"){
      frm.set_query('account_paid_from', function(){
        return {
          filters: {
            is_group: 0,
            parent_account: 'Current Assets'
          }
        }
      });
      frm.set_query('account_paid_to', function(){
        return {
          filters: {
            is_group: 0,
            parent_account: 'Accounts Payable'
          }
        }
      });
    }

		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__("View General Ledger"), function(){
				frappe.route_options = {
					"from_date": frm.doc.posting_date,
					"to_date": frm.doc.posting_date
				};
				frappe.set_route("query-report", "General Ledger Report")
			});
		}
  }
});
