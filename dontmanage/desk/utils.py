# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def validate_route_conflict(doctype, name):
	"""
	Raises exception if name clashes with routes from other documents for /app routing
	"""

	if dontmanage.flags.in_migrate:
		return

	all_names = []
	for _doctype in ["Page", "Workspace", "DocType"]:
		all_names.extend(
			[slug(d) for d in dontmanage.get_all(_doctype, pluck="name") if (doctype != _doctype and d != name)]
		)

	if slug(name) in all_names:
		dontmanage.msgprint(dontmanage._("Name already taken, please set a new name"))
		raise dontmanage.NameError


def slug(name):
	return name.lower().replace(" ", "-")
