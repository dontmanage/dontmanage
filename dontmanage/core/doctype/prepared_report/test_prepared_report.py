# Copyright (c) 2018, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import json

import dontmanage
from dontmanage.tests.utils import DontManageTestCase


class TestPreparedReport(DontManageTestCase):
	def setUp(self):
		self.report = dontmanage.get_doc({"doctype": "Report", "name": "Permitted Documents For User"})
		self.filters = {"user": "Administrator", "doctype": "Role"}
		self.prepared_report_doc = dontmanage.get_doc(
			{
				"doctype": "Prepared Report",
				"report_name": self.report.name,
				"filters": json.dumps(self.filters),
				"ref_report_doctype": self.report.name,
			}
		).insert()

	def tearDown(self):
		dontmanage.set_user("Administrator")
		self.prepared_report_doc.delete()

	def test_for_creation(self):
		self.assertTrue("QUEUED" == self.prepared_report_doc.status.upper())
		self.assertTrue(self.prepared_report_doc.report_start_time)
