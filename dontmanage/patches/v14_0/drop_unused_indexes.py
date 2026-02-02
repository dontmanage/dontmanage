"""
This patch just drops some known indexes which aren't being used anymore or never were used.
"""

import dontmanage
from dontmanage.database.utils import drop_index_if_exists

UNUSED_INDEXES = [
	("Comment", ["link_doctype", "link_name"]),
	("Activity Log", ["link_doctype", "link_name"]),
]


def execute():
	if dontmanage.db.db_type == "postgres":
		return

	db_tables = dontmanage.db.get_tables(cached=False)

	# All parent indexes
	parent_doctypes = dontmanage.get_all(
		"DocType",
		{"istable": 0, "is_virtual": 0, "issingle": 0},
		pluck="name",
	)
	db_tables = dontmanage.db.get_tables(cached=False)

	for doctype in parent_doctypes:
		table = f"tab{doctype}"
		if table not in db_tables:
			continue
		drop_index_if_exists(table, "parent")

	# Unused composite indexes
	for doctype, index_fields in UNUSED_INDEXES:
		table = f"tab{doctype}"
		index_name = dontmanage.db.get_index_name(index_fields)
		if table not in db_tables:
			continue
		drop_index_if_exists(table, index_name)
