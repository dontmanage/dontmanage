# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	"""Enable all the existing Client script"""

	dontmanage.db.sql(
		"""
		UPDATE `tabClient Script` SET enabled=1
	"""
	)
