frappe.treeview_settings["Account"] = {
  ignore_fields:["parent_account"],
  onrender: function(node){
    console.log(node.data)
  }
}
