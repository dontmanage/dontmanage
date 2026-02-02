# Copyright (c) 2022, DontManage and Contributors
# License: MIT. See LICENSE


import dontmanage
from dontmanage.model import data_field_options


def execute():
	custom_field = dontmanage.qb.DocType("Custom Field")
	(
		dontmanage.qb.update(custom_field)
		.set(custom_field.options, None)
		.where((custom_field.fieldtype == "Data") & (custom_field.options.notin(data_field_options)))
	).run()
