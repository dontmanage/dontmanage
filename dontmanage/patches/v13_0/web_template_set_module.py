# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	"""Set default module for standard Web Template, if none."""
	dontmanage.reload_doc("website", "doctype", "Web Template Field")
	dontmanage.reload_doc("website", "doctype", "web_template")

	standard_templates = dontmanage.get_list("Web Template", {"standard": 1})
	for template in standard_templates:
		doc = dontmanage.get_doc("Web Template", template.name)
		if not doc.module:
			doc.module = "Website"
			doc.save()
