import dontmanage


def execute():
	column = "apply_user_permissions"
	to_remove = ["DocPerm", "Custom DocPerm"]

	for doctype in to_remove:
		if dontmanage.db.table_exists(doctype):
			if column in dontmanage.db.get_table_columns(doctype):
				dontmanage.db.sql(f"alter table `tab{doctype}` drop column {column}")

	dontmanage.reload_doc("core", "doctype", "docperm", force=True)
	dontmanage.reload_doc("core", "doctype", "custom_docperm", force=True)
