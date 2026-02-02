# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage


def add_custom_field(doctype, fieldname, fieldtype="Data", options=None):
	dontmanage.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"options": options,
		}
	).insert()


def clear_custom_fields(doctype):
	dontmanage.db.delete("Custom Field", {"dt": doctype})
	dontmanage.clear_cache(doctype=doctype)
