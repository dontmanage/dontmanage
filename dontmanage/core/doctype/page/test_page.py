# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import os
import unittest
from unittest.mock import patch

import dontmanage
from dontmanage.tests import IntegrationTestCase


class TestPage(IntegrationTestCase):
	def test_naming(self):
		self.assertRaises(
			dontmanage.NameError,
			dontmanage.get_doc(doctype="Page", page_name="DocType", module="Core").insert,
		)

	@unittest.skipUnless(
		os.access(dontmanage.get_app_path("dontmanage"), os.W_OK), "Only run if dontmanage app paths is writable"
	)
	@patch.dict(dontmanage.conf, {"developer_mode": 1})
	def test_trashing(self):
		page = dontmanage.new_doc("Page", page_name=dontmanage.generate_hash(), module="Core").insert()

		page.delete()
		dontmanage.db.commit()

		module_path = dontmanage.get_module_path(page.module)
		dir_path = os.path.join(module_path, "page", dontmanage.scrub(page.name))

		self.assertFalse(os.path.exists(dir_path))
