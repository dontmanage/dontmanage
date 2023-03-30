# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils.logger import sanitized_dict

# test_records = dontmanage.get_test_records('Error Snapshot')


class TestErrorSnapshot(DontManageTestCase):
	def test_form_dict_sanitization(self):
		self.assertNotEqual(sanitized_dict({"pwd": "SECRET", "usr": "WHAT"}).get("pwd"), "SECRET")
