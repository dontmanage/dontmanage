# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests import IntegrationTestCase
from dontmanage.utils.data import add_to_date, today


class TestDocumentLocks(IntegrationTestCase):
	def test_locking(self):
		todo = dontmanage.get_doc(doctype="ToDo", description="test").insert()
		todo_1 = dontmanage.get_doc("ToDo", todo.name)

		todo.lock()
		self.assertRaises(dontmanage.DocumentLockedError, todo_1.lock)
		todo.unlock()

		todo_1.lock()
		self.assertRaises(dontmanage.DocumentLockedError, todo.lock)
		todo_1.unlock()

	def test_operations_on_locked_documents(self):
		todo = dontmanage.get_doc(doctype="ToDo", description="testing operations").insert()
		todo.lock()

		with self.assertRaises(dontmanage.DocumentLockedError):
			todo.description = "Random"
			todo.save()

		# Checking for persistant locks across all instances.
		doc = dontmanage.get_doc("ToDo", todo.name)
		self.assertEqual(doc.is_locked, True)

		with self.assertRaises(dontmanage.DocumentLockedError):
			doc.description = "Random"
			doc.save()

		doc.unlock()
		self.assertEqual(doc.is_locked, False)
		self.assertEqual(todo.is_locked, False)

	def test_locks_auto_expiry(self):
		todo = dontmanage.get_doc(doctype="ToDo", description=dontmanage.generate_hash()).insert()
		todo.lock()

		self.assertRaises(dontmanage.DocumentLockedError, todo.lock)

		with self.freeze_time(add_to_date(today(), days=3)):
			todo.lock()
