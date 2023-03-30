# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
import dontmanage.share
from dontmanage.automation.doctype.auto_repeat.test_auto_repeat import create_submittable_doctype
from dontmanage.tests.utils import DontManageTestCase

test_dependencies = ["User"]


class TestDocShare(DontManageTestCase):
	def setUp(self):
		self.user = "test@example.com"
		self.event = dontmanage.get_doc(
			{
				"doctype": "Event",
				"subject": "test share event",
				"starts_on": "2015-01-01 10:00:00",
				"event_type": "Private",
			}
		).insert()

	def tearDown(self):
		dontmanage.set_user("Administrator")
		self.event.delete()

	def test_add(self):
		# user not shared
		self.assertTrue(self.event.name not in dontmanage.share.get_shared("Event", self.user))
		dontmanage.share.add("Event", self.event.name, self.user)
		self.assertTrue(self.event.name in dontmanage.share.get_shared("Event", self.user))

	def test_doc_permission(self):
		dontmanage.set_user(self.user)
		self.assertFalse(self.event.has_permission())

		dontmanage.set_user("Administrator")
		dontmanage.share.add("Event", self.event.name, self.user)

		dontmanage.set_user(self.user)
		self.assertTrue(self.event.has_permission())

	def test_share_permission(self):
		dontmanage.share.add("Event", self.event.name, self.user, write=1, share=1)

		dontmanage.set_user(self.user)
		self.assertTrue(self.event.has_permission("share"))

		# test cascade
		self.assertTrue(self.event.has_permission("read"))
		self.assertTrue(self.event.has_permission("write"))

	def test_set_permission(self):
		dontmanage.share.add("Event", self.event.name, self.user)

		dontmanage.set_user(self.user)
		self.assertFalse(self.event.has_permission("share"))

		dontmanage.set_user("Administrator")
		dontmanage.share.set_permission("Event", self.event.name, self.user, "share")

		dontmanage.set_user(self.user)
		self.assertTrue(self.event.has_permission("share"))

	def test_permission_to_share(self):
		dontmanage.set_user(self.user)
		self.assertRaises(dontmanage.PermissionError, dontmanage.share.add, "Event", self.event.name, self.user)

		dontmanage.set_user("Administrator")
		dontmanage.share.add("Event", self.event.name, self.user, write=1, share=1)

		# test not raises
		dontmanage.set_user(self.user)
		dontmanage.share.add("Event", self.event.name, "test1@example.com", write=1, share=1)

	def test_remove_share(self):
		dontmanage.share.add("Event", self.event.name, self.user, write=1, share=1)

		dontmanage.set_user(self.user)
		self.assertTrue(self.event.has_permission("share"))

		dontmanage.set_user("Administrator")
		dontmanage.share.remove("Event", self.event.name, self.user)

		dontmanage.set_user(self.user)
		self.assertFalse(self.event.has_permission("share"))

	def test_share_with_everyone(self):
		self.assertTrue(self.event.name not in dontmanage.share.get_shared("Event", self.user))

		dontmanage.share.set_permission("Event", self.event.name, None, "read", everyone=1)
		self.assertTrue(self.event.name in dontmanage.share.get_shared("Event", self.user))
		self.assertTrue(self.event.name in dontmanage.share.get_shared("Event", "test1@example.com"))
		self.assertTrue(self.event.name not in dontmanage.share.get_shared("Event", "Guest"))

		dontmanage.share.set_permission("Event", self.event.name, None, "read", value=0, everyone=1)
		self.assertTrue(self.event.name not in dontmanage.share.get_shared("Event", self.user))
		self.assertTrue(self.event.name not in dontmanage.share.get_shared("Event", "test1@example.com"))
		self.assertTrue(self.event.name not in dontmanage.share.get_shared("Event", "Guest"))

	def test_share_with_submit_perm(self):
		doctype = "Test DocShare with Submit"
		create_submittable_doctype(doctype, submit_perms=0)

		submittable_doc = dontmanage.get_doc(
			dict(doctype=doctype, test="test docshare with submit")
		).insert()

		dontmanage.set_user(self.user)
		self.assertFalse(dontmanage.has_permission(doctype, "submit", user=self.user))

		dontmanage.set_user("Administrator")
		dontmanage.share.add(doctype, submittable_doc.name, self.user, submit=1)

		dontmanage.set_user(self.user)
		self.assertTrue(
			dontmanage.has_permission(doctype, "submit", doc=submittable_doc.name, user=self.user)
		)

		# test cascade
		self.assertTrue(dontmanage.has_permission(doctype, "read", doc=submittable_doc.name, user=self.user))
		self.assertTrue(
			dontmanage.has_permission(doctype, "write", doc=submittable_doc.name, user=self.user)
		)

		dontmanage.share.remove(doctype, submittable_doc.name, self.user)

	def test_share_int_pk(self):
		test_doc = dontmanage.new_doc("Console Log")

		test_doc.insert()
		dontmanage.share.add("Console Log", test_doc.name, self.user)

		dontmanage.set_user(self.user)
		self.assertIn(
			str(test_doc.name), [str(name) for name in dontmanage.get_list("Console Log", pluck="name")]
		)

		test_doc.reload()
		self.assertTrue(test_doc.has_permission("read"))
