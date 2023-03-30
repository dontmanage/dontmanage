# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.reload_doc("core", "doctype", "DocField")

	if dontmanage.db.has_column("DocField", "show_days"):
		dontmanage.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_days = 1 WHERE show_days = 0
		"""
		)
		dontmanage.db.sql_ddl("alter table tabDocField drop column show_days")

	if dontmanage.db.has_column("DocField", "show_seconds"):
		dontmanage.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_seconds = 1 WHERE show_seconds = 0
		"""
		)
		dontmanage.db.sql_ddl("alter table tabDocField drop column show_seconds")

	dontmanage.clear_cache(doctype="DocField")
