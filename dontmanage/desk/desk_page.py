# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


@dontmanage.whitelist()
def get(name):
	"""
	Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = dontmanage.get_doc("Page", name)
	if page.is_permitted():
		page.load_assets()
		docs = dontmanage._dict(page.as_dict())
		if getattr(page, "_dynamic_page", None):
			docs["_dynamic_page"] = 1

		return docs
	else:
		dontmanage.response["403"] = 1
		raise dontmanage.PermissionError("No read permission for Page %s" % (page.title or name))


@dontmanage.whitelist(allow_guest=True)
def getpage():
	"""
	Load the page from `dontmanage.form` and send it via `dontmanage.response`
	"""
	page = dontmanage.form_dict.get("name")
	doc = get(page)

	dontmanage.response.docs.append(doc)
