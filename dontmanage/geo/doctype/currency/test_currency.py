# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

# pre loaded

import dontmanage
from dontmanage.tests.utils import DontManageTestCase


class TestUser(DontManageTestCase):
	def test_default_currency_on_setup(self):
		usd = dontmanage.get_doc("Currency", "USD")
		self.assertDocumentEqual({"enabled": 1, "fraction": "Cent"}, usd)
