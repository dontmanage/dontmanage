from contextlib import contextmanager
from random import choice

import dontmanage
from dontmanage.model import core_doctypes_list, get_permitted_fields
from dontmanage.model.utils import get_fetch_values
from dontmanage.tests.utils import DontManageTestCase


class TestModelUtils(DontManageTestCase):
	def test_get_fetch_values(self):
		doctype = "ToDo"

		# no fields to fetch
		self.assertEqual(get_fetch_values(doctype, "role", "System Manager"), {})

		# no value
		self.assertEqual(get_fetch_values(doctype, "assigned_by", None), {"assigned_by_full_name": None})

		# no db values
		self.assertEqual(
			get_fetch_values(doctype, "assigned_by", "~not-a-user~"), {"assigned_by_full_name": None}
		)

		# valid db values
		user = "test@example.com"
		full_name = dontmanage.db.get_value("User", user, "full_name")

		self.assertEqual(
			get_fetch_values(doctype, "assigned_by", user), {"assigned_by_full_name": full_name}
		)

	def test_get_permitted_fields(self):
		# Administrator should have access to all fields in ToDo
		todo_all_fields = get_permitted_fields("ToDo", user="Administrator")
		todo_all_columns = dontmanage.get_meta("ToDo").get_valid_columns()
		self.assertListEqual(todo_all_fields, todo_all_columns)

		# Guest should have access to no fields in ToDo
		with set_user("Guest"):
			guest_permitted_fields = get_permitted_fields("ToDo")
			self.assertEqual(guest_permitted_fields, [])

		# everyone should have access to all fields of core doctypes
		with set_user("Guest"):
			picked_doctype = choice(core_doctypes_list)
			core_permitted_fields = get_permitted_fields(picked_doctype)
			picked_doctype_all_columns = dontmanage.get_meta(picked_doctype).get_valid_columns()
			self.assertSequenceEqual(core_permitted_fields, picked_doctype_all_columns)

		# access to child tables' fields is restricted to no fields unless parent is passed & permitted
		with set_user("Administrator"):
			without_parent_fields = get_permitted_fields("Installed Application")
			with_parent_fields = get_permitted_fields(
				"Installed Application", parenttype="Installed Applications"
			)
			child_all_fields = dontmanage.get_meta("Installed Application").get_valid_columns()
			self.assertEqual(without_parent_fields, [])
			self.assertLess(len(without_parent_fields), len(with_parent_fields))
			self.assertSequenceEqual(set(with_parent_fields), set(child_all_fields))

		# guest has access to no fields
		with set_user("Guest"):
			self.assertEqual(get_permitted_fields("Installed Application"), [])
			self.assertEqual(
				get_permitted_fields("Installed Application", parenttype="Installed Applications"), []
			)


@contextmanager
def set_user(user: str):
	past_user = dontmanage.session.user or "Administrator"
	dontmanage.set_user(user)
	yield
	dontmanage.set_user(past_user)
