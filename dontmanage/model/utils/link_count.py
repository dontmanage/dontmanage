# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage

ignore_doctypes = ("DocType", "Print Format", "Role", "Module Def", "Communication", "ToDo")


def notify_link_count(doctype, name):
	"""updates link count for given document"""
	if hasattr(dontmanage.local, "link_count"):
		if (doctype, name) in dontmanage.local.link_count:
			dontmanage.local.link_count[(doctype, name)] += 1
		else:
			dontmanage.local.link_count[(doctype, name)] = 1


def flush_local_link_count():
	"""flush from local before ending request"""
	if not getattr(dontmanage.local, "link_count", None):
		return

	link_count = dontmanage.cache().get_value("_link_count")
	if not link_count:
		link_count = {}

		for key, value in dontmanage.local.link_count.items():
			if key in link_count:
				link_count[key] += dontmanage.local.link_count[key]
			else:
				link_count[key] = dontmanage.local.link_count[key]

	dontmanage.cache().set_value("_link_count", link_count)


def update_link_count():
	"""increment link count in the `idx` column for the given document"""
	link_count = dontmanage.cache().get_value("_link_count")

	if link_count:
		for key, count in link_count.items():
			if key[0] not in ignore_doctypes:
				try:
					dontmanage.db.sql(
						f"update `tab{key[0]}` set idx = idx + {count} where name=%s",
						key[1],
						auto_commit=1,
					)
				except Exception as e:
					if not dontmanage.db.is_table_missing(e):  # table not found, single
						raise e
	# reset the count
	dontmanage.cache().delete_value("_link_count")
