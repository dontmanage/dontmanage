# Copyright (c) 2015, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.contacts.doctype.address_template.address_template import get_default_address_template
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils.jinja import validate_template


class TestAddressTemplate(DontManageTestCase):
	def setUp(self) -> None:
		dontmanage.db.delete("Address Template", {"country": "India"})
		dontmanage.db.delete("Address Template", {"country": "Brazil"})

	def test_default_address_template(self):
		validate_template(get_default_address_template())

	def test_default_is_unset(self):
		dontmanage.get_doc({"doctype": "Address Template", "country": "India", "is_default": 1}).insert()

		self.assertEqual(dontmanage.db.get_value("Address Template", "India", "is_default"), 1)

		dontmanage.get_doc({"doctype": "Address Template", "country": "Brazil", "is_default": 1}).insert()

		self.assertEqual(dontmanage.db.get_value("Address Template", "India", "is_default"), 0)
		self.assertEqual(dontmanage.db.get_value("Address Template", "Brazil", "is_default"), 1)

	def test_delete_address_template(self):
		india = dontmanage.get_doc({"doctype": "Address Template", "country": "India", "is_default": 0}).insert()

		brazil = dontmanage.get_doc(
			{"doctype": "Address Template", "country": "Brazil", "is_default": 1}
		).insert()

		india.reload()  # might have been modified by the second template
		india.delete()  # should not raise an error

		self.assertRaises(dontmanage.ValidationError, brazil.delete)
