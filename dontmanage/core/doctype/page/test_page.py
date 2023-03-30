# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests.utils import DontManageTestCase

test_records = dontmanage.get_test_records("Page")


class TestPage(DontManageTestCase):
	def test_naming(self):
		self.assertRaises(
			dontmanage.NameError,
			dontmanage.get_doc(dict(doctype="Page", page_name="DocType", module="Core")).insert,
		)
		self.assertRaises(
			dontmanage.NameError,
			dontmanage.get_doc(dict(doctype="Page", page_name="Settings", module="Core")).insert,
		)
