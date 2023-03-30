# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.desk.form.linked_with import get_linked_docs, get_linked_doctypes
from dontmanage.tests.utils import DontManageTestCase


class TestForm(DontManageTestCase):
	def test_linked_with(self):
		results = get_linked_docs("Role", "System Manager", linkinfo=get_linked_doctypes("Role"))
		self.assertTrue("User" in results)
		self.assertTrue("DocType" in results)


if __name__ == "__main__":
	import unittest

	dontmanage.connect()
	unittest.main()
