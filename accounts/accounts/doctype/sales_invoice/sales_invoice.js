// Copyright (c) 2019, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
	refresh: function(frm) {
		frm.trigger('total_amount')
    frm.set_query("customer", function(){
      return {
        filters: {
          party_type: 'Customer'
        }
      }
    });
    frm.set_query("debit_to", function(){
      return {
        filters: {
          is_group: 0,
          parent_account: 'Accounts Receivable'
        }
      }
    });
    frm.set_query("income_account", function(){
      return{
        filters: {
          is_group: 0,
          root_type: 'Income'
        }
      }
    });
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__('Make Payment Entry'), function(){
				frappe.route_options = {"payment_type": "Receive", "party_type":"Customer", "party": frm.doc.customer, "account_paid_from": frm.doc.debit_to, "amount_paid": frm.doc.total_amount};
				frappe.set_route("Form", "Payment Entry","New Payment Entry");
		 });
 		}
	 if(frm.doc.docstatus == 1){
		 frm.add_custom_button(__("View General Ledger"), function(){
			 frappe.route_options = {
				 "from_date": frm.doc.posting_date,
				 "to_date": frm.doc.posting_date,
			 };
			 frappe.set_route("query-report", "General Ledger Report")
		 });
 	}
 },

  total_amount: function(frm) {
    let total_quantity = 0
    let total_amount = 0;
    frm.doc.items.forEach((d) => {
        if(d.quantity) total_quantity += flt(d.quantity);
        if(d.amount) total_amount += flt(d.amount);
    })
    frm.set_value('total_quantity', total_quantity);
    frm.set_value('total_amount', total_amount);
    frm.refresh_fields();
  }
});

frappe.ui.form.on('Sales Invoice Item', {
  item: function(frm, cdt, cdn) {
    let items = locals[cdt][cdn];
    frappe.call("frappe.client.get", {
      doctype: "Item",
      name: items.item
    }).then((res) => {
      items.rate = res.message.standard_selling_rate;
      items.quantity = items.quantity || 1;
      items.amount = items.rate * items.quantity;
      frm.refresh_field('items');
      frm.trigger('total_amount')
    })
  },

  quantity: function(frm,cdt,cdn){
    let d = locals[cdt][cdn];
    d.amount = d.rate * d.quantity;
    frm.refresh_field('items');
    frm.trigger('total_amount')
  },

  rate: function(frm,cdt,cdn){
    let d = locals[cdt][cdn];
    d.amount = d.rate * d.quantity;
    frm.refresh_field('items');
    frm.trigger('total_amount')
  }
});
