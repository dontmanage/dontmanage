import dontmanage


def execute():
	doctype = "Top Bar Item"
	if not dontmanage.db.table_exists(doctype) or not dontmanage.db.has_column(doctype, "target"):
		return

	dontmanage.reload_doc("website", "doctype", "top_bar_item")
	dontmanage.db.set_value(doctype, {"target": 'target = "_blank"'}, "open_in_new_tab", 1)
