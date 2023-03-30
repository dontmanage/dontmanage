# Copyright (c) 2015, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests.utils import DontManageTestCase

# test_records = dontmanage.get_test_records('Error Log')


class TestErrorLog(DontManageTestCase):
	def test_error_log(self):
		"""let's do an error log on error log?"""
		doc = dontmanage.new_doc("Error Log")
		error = doc.log_error("This is an error")
		self.assertEqual(error.doctype, "Error Log")
