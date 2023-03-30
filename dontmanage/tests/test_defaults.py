# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
from contextlib import contextmanager

import dontmanage
from dontmanage.defaults import *
from dontmanage.tests.utils import DontManageTestCase


class TestDefaults(DontManageTestCase):
	def test_global(self):
		clear_user_default("key1")
		set_global_default("key1", "value1")
		self.assertEqual(get_global_default("key1"), "value1")

		set_global_default("key1", "value2")
		self.assertEqual(get_global_default("key1"), "value2")

		add_global_default("key1", "value3")
		self.assertEqual(get_global_default("key1"), "value2")
		self.assertEqual(get_defaults()["key1"], ["value2", "value3"])
		self.assertEqual(get_user_default_as_list("key1"), ["value2", "value3"])

	def test_user(self):
		set_user_default("key1", "2value1")
		self.assertEqual(get_user_default_as_list("key1"), ["2value1"])

		set_user_default("key1", "2value2")
		self.assertEqual(get_user_default("key1"), "2value2")

		add_user_default("key1", "3value3")
		self.assertEqual(get_user_default("key1"), "2value2")
		self.assertEqual(get_user_default_as_list("key1"), ["2value2", "3value3"])

	def test_global_if_not_user(self):
		set_global_default("key4", "value4")
		self.assertEqual(get_user_default("key4"), "value4")

	def test_clear(self):
		set_user_default("key5", "value5")
		self.assertEqual(get_user_default("key5"), "value5")
		clear_user_default("key5")
		self.assertEqual(get_user_default("key5"), None)

	def test_clear_global(self):
		set_global_default("key6", "value6")
		self.assertEqual(get_user_default("key6"), "value6")

		clear_default("key6", value="value6")
		self.assertEqual(get_user_default("key6"), None)

	def test_user_permission_on_defaults(self):
		self.assertEqual(get_global_default("language"), "en")
		self.assertEqual(get_user_default("language"), "en")
		self.assertEqual(get_user_default_as_list("language"), ["en"])

		with as_restricted_user():
			self.assertEqual(get_global_default("language"), None)
			self.assertEqual(get_user_default("language"), None)
			self.assertEqual(get_user_default_as_list("language"), [])


@contextmanager
def as_restricted_user():
	old_user = dontmanage.session.user
	user = "test@example.com"

	perm_doc = dontmanage.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": "Language",
			"for_value": "en-GB",
		}
	).insert(ignore_permissions=True)

	dontmanage.set_user(user)

	yield

	perm_doc.delete(ignore_permissions=True)
	dontmanage.set_user(old_user)
