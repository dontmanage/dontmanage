# Copyright (c) 2022, DontManage Technologies and contributors
# For license information, please see license.txt


from dontmanage.core.report.database_storage_usage_by_tables.database_storage_usage_by_tables import (
	execute,
)
from dontmanage.tests.utils import DontManageTestCase


class TestDBUsageReport(DontManageTestCase):
	def test_basic_query(self):
		_, data = execute()
		tables = [d.table for d in data]
		self.assertFalse({"tabUser", "tabDocField"}.difference(tables))
