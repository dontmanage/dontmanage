# Copyright (c) 2022, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.config import get_modules_from_all_apps_for_user
from dontmanage.tests.utils import DontManageTestCase


class TestConfig(DontManageTestCase):
	def test_get_modules(self):
		dontmanage_modules = dontmanage.get_all("Module Def", filters={"app_name": "dontmanage"}, pluck="name")
		all_modules_data = get_modules_from_all_apps_for_user()
		all_modules = [x["module_name"] for x in all_modules_data]
		self.assertIsInstance(all_modules_data, list)
		self.assertFalse([x for x in dontmanage_modules if x not in all_modules])
