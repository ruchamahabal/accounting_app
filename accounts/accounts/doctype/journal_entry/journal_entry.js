// Copyright (c) 2019, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Journal Entry', {
	refresh: function(frm) {
    frm.set_query("account", "accounting_entries", function() {
      return {
        filters: {
          is_group: 0
        }
      };
    });
	},
});

frappe.ui.form.on('Journal Entry Account', {
  debit: function(frm, cdt, cdn){
    var d = locals[cdt][cdn];
    var total = 0, diff = 0;
    frm.doc.accounting_entries.forEach(function(d) {
       if(d.debit) total += d.debit;
     });
    frm.set_value("total_debit", total);
    refresh_field("total_debit");
    if (frm.doc.total_credit){
      diff = frm.doc.total_debit - frm.doc.total_credit
      frm.set_value("debit_credit_diff", diff);
      refresh_field("debit_credit_diff");
    }
    else{
        frm.set_value("total_credit", 0.00);
        frm.set_value("debit_credit_diff", frm.doc.total_debit);
    }
  },
  credit: function(frm, cdt, cdn){
    var d = locals[cdt][cdn];
    var total = 0, diff = 0;
    frm.doc.accounting_entries.forEach(function(d) {
      if(d.credit) total += d.credit;
    });
    frm.set_value("total_credit", total);
    refresh_field("total_credit");
    if (frm.doc.total_debit){
      diff = frm.doc.total_debit - frm.doc.total_credit
      frm.set_value("debit_credit_diff", diff);
      refresh_field("debit_credit_diff");
    }
    else{
        frm.set_value("total_debit", 0.00);
        frm.set_value("debit_credit_diff", frm.doc.debit_credit_diff);
    }
  },
  accounting_entries_remove: function(frm, cdt, cdn){
    var total_debit=0, total_credit = 0;
    frm.doc.accounting_entries.forEach(function(d){
        if(d.debit) total_debit += d.debit;
        if(d.credit) total_credit += d.credit;
    })
    frm.set_value("total_debit", total_debit);
    refresh_field("total_debit");

    frm.set_value("total_credit", total_credit);
    refresh_field("total_credit")

    frm.set_value("debit_credit_diff", total_debit - total_credit);
    refresh_field("debit_credit_diff");
  }
});
