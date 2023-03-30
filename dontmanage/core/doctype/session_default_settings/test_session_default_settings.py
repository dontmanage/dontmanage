# Copyright (c) 2019, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.core.doctype.session_default_settings.session_default_settings import (
	clear_session_defaults,
	set_session_default_values,
)
from dontmanage.tests.utils import DontManageTestCase


class TestSessionDefaultSettings(DontManageTestCase):
	def test_set_session_default_settings(self):
		dontmanage.set_user("Administrator")
		settings = dontmanage.get_single("Session Default Settings")
		settings.session_defaults = []
		settings.append("session_defaults", {"ref_doctype": "Role"})
		settings.save()

		set_session_default_values({"role": "Website Manager"})

		todo = dontmanage.get_doc(
			dict(doctype="ToDo", description="test session defaults set", assigned_by="Administrator")
		).insert()
		self.assertEqual(todo.role, "Website Manager")

	def test_clear_session_defaults(self):
		clear_session_defaults()
		todo = dontmanage.get_doc(
			dict(doctype="ToDo", description="test session defaults cleared", assigned_by="Administrator")
		).insert()
		self.assertNotEqual(todo.role, "Website Manager")
