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


def has_permission(page):
	if dontmanage.session.user == "Administrator" or "System Manager" in dontmanage.get_roles():
		return True

	page_roles = [d.role for d in page.get("roles")]
	if page_roles:
		if dontmanage.session.user == "Guest" and "Guest" not in page_roles:
			return False
		elif not set(page_roles).intersection(set(dontmanage.get_roles())):
			# check if roles match
			return False

	if not dontmanage.has_permission("Page", ptype="read", doc=page):
		# check if there are any user_permissions
		return False
	else:
		# hack for home pages! if no Has Roles, allow everyone to see!
		return True
