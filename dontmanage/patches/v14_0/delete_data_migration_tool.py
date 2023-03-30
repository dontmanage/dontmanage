# Copyright (c) 2022, DontManage and Contributors
# MIT License. See license.txt

import dontmanage


def execute():
	doctypes = dontmanage.get_all("DocType", {"module": "Data Migration", "custom": 0}, pluck="name")
	for doctype in doctypes:
		dontmanage.delete_doc("DocType", doctype, ignore_missing=True)

	dontmanage.delete_doc("Module Def", "Data Migration", ignore_missing=True, force=True)
