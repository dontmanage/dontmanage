# Copyright (c) 2020, DontManage Technologies and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.core.doctype.installed_applications.installed_applications import (
	InvalidAppOrder,
	update_installed_apps_order,
)
from dontmanage.tests.utils import DontManageTestCase


class TestInstalledApplications(DontManageTestCase):
	def test_order_change(self):
		update_installed_apps_order(["dontmanage"])
		self.assertRaises(InvalidAppOrder, update_installed_apps_order, [])
		self.assertRaises(InvalidAppOrder, update_installed_apps_order, ["dontmanage", "deepmind"])
