# Copyright (c) 2015, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.contacts.doctype.address.address import get_address_display
from dontmanage.tests.utils import DontManageTestCase


class TestAddress(DontManageTestCase):
	def test_template_works(self):
		if not dontmanage.db.exists("Address Template", "India"):
			dontmanage.get_doc({"doctype": "Address Template", "country": "India", "is_default": 1}).insert()

		if not dontmanage.db.exists("Address", "_Test Address-Office"):
			dontmanage.get_doc(
				{
					"address_line1": "_Test Address Line 1",
					"address_title": "_Test Address",
					"address_type": "Office",
					"city": "_Test City",
					"state": "Test State",
					"country": "India",
					"doctype": "Address",
					"is_primary_address": 1,
					"phone": "+91 0000000000",
				}
			).insert()

		address = dontmanage.get_list("Address")[0].name
		display = get_address_display(dontmanage.get_doc("Address", address).as_dict())
		self.assertTrue(display)
