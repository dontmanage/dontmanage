# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _


@dontmanage.whitelist()
def get_all_nodes(doctype, label, parent, tree_method, **filters):
	"""Recursively gets all data from tree nodes"""

	if "cmd" in filters:
		del filters["cmd"]
	filters.pop("data", None)

	tree_method = dontmanage.get_attr(tree_method)

	if tree_method not in dontmanage.whitelisted:
		dontmanage.throw(_("Not Permitted"), dontmanage.PermissionError)

	data = tree_method(doctype, parent, **filters)
	out = [dict(parent=label, data=data)]

	if "is_root" in filters:
		del filters["is_root"]
	to_check = [d.get("value") for d in data if d.get("expandable")]

	while to_check:
		parent = to_check.pop()
		data = tree_method(doctype, parent, is_root=False, **filters)
		out.append(dict(parent=parent, data=data))
		for d in data:
			if d.get("expandable"):
				to_check.append(d.get("value"))

	return out


@dontmanage.whitelist()
def get_children(doctype, parent="", **filters):
	return _get_children(doctype, parent)


def _get_children(doctype, parent="", ignore_permissions=False):
	parent_field = "parent_" + doctype.lower().replace(" ", "_")
	filters = [[f"ifnull(`{parent_field}`,'')", "=", parent], ["docstatus", "<", 2]]

	meta = dontmanage.get_meta(doctype)

	return dontmanage.get_list(
		doctype,
		fields=[
			"name as value",
			"{} as title".format(meta.get("title_field") or "name"),
			"is_group as expandable",
		],
		filters=filters,
		order_by="name",
		ignore_permissions=ignore_permissions,
	)


@dontmanage.whitelist()
def add_node():
	args = make_tree_args(**dontmanage.form_dict)
	doc = dontmanage.get_doc(args)

	doc.save()


def make_tree_args(**kwarg):
	kwarg.pop("cmd", None)

	doctype = kwarg["doctype"]
	parent_field = "parent_" + doctype.lower().replace(" ", "_")

	if kwarg["is_root"] == "false":
		kwarg["is_root"] = False
	if kwarg["is_root"] == "true":
		kwarg["is_root"] = True

	kwarg.update({parent_field: kwarg.get("parent") or kwarg.get(parent_field)})

	return dontmanage._dict(kwarg)
