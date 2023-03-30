# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	if not dontmanage.db.table_exists("Data Import"):
		return

	meta = dontmanage.get_meta("Data Import")
	# if Data Import is the new one, return early
	if meta.fields[1].fieldname == "import_type":
		return

	dontmanage.db.sql("DROP TABLE IF EXISTS `tabData Import Legacy`")
	dontmanage.rename_doc("DocType", "Data Import", "Data Import Legacy")
	dontmanage.db.commit()
	dontmanage.db.sql("DROP TABLE IF EXISTS `tabData Import`")
	dontmanage.rename_doc("DocType", "Data Import Beta", "Data Import")
