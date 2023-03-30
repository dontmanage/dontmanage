# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests.utils import DontManageTestCase


class TestDocumentLocks(DontManageTestCase):
	def test_locking(self):
		todo = dontmanage.get_doc(dict(doctype="ToDo", description="test")).insert()
		todo_1 = dontmanage.get_doc("ToDo", todo.name)

		todo.lock()
		self.assertRaises(dontmanage.DocumentLockedError, todo_1.lock)
		todo.unlock()

		todo_1.lock()
		self.assertRaises(dontmanage.DocumentLockedError, todo.lock)
		todo_1.unlock()
