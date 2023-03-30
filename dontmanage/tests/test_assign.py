# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
import dontmanage.desk.form.assign_to
from dontmanage.automation.doctype.assignment_rule.test_assignment_rule import make_note
from dontmanage.desk.form.load import get_assignments
from dontmanage.desk.listview import get_group_by_count
from dontmanage.tests.utils import DontManageTestCase


class TestAssign(DontManageTestCase):
	def test_assign(self):
		todo = dontmanage.get_doc({"doctype": "ToDo", "description": "test"}).insert()
		if not dontmanage.db.exists("User", "test@example.com"):
			dontmanage.get_doc({"doctype": "User", "email": "test@example.com", "first_name": "Test"}).insert()

		added = assign(todo, "test@example.com")

		self.assertTrue("test@example.com" in [d.owner for d in added])

		removed = dontmanage.desk.form.assign_to.remove(todo.doctype, todo.name, "test@example.com")

		# assignment is cleared
		assignments = dontmanage.desk.form.assign_to.get(dict(doctype=todo.doctype, name=todo.name))
		self.assertEqual(len(assignments), 0)

	def test_assignment_count(self):
		dontmanage.db.delete("ToDo")

		if not dontmanage.db.exists("User", "test_assign1@example.com"):
			dontmanage.get_doc(
				{
					"doctype": "User",
					"email": "test_assign1@example.com",
					"first_name": "Test",
					"roles": [{"role": "System Manager"}],
				}
			).insert()

		if not dontmanage.db.exists("User", "test_assign2@example.com"):
			dontmanage.get_doc(
				{
					"doctype": "User",
					"email": "test_assign2@example.com",
					"first_name": "Test",
					"roles": [{"role": "System Manager"}],
				}
			).insert()

		note = make_note()
		assign(note, "test_assign1@example.com")

		note = make_note(dict(public=1))
		assign(note, "test_assign2@example.com")

		note = make_note(dict(public=1))
		assign(note, "test_assign2@example.com")

		note = make_note()
		assign(note, "test_assign2@example.com")

		data = {d.name: d.count for d in get_group_by_count("Note", "[]", "assigned_to")}

		self.assertTrue("test_assign1@example.com" in data)
		self.assertEqual(data["test_assign1@example.com"], 1)
		self.assertEqual(data["test_assign2@example.com"], 3)

		data = {d.name: d.count for d in get_group_by_count("Note", '[{"public": 1}]', "assigned_to")}

		self.assertFalse("test_assign1@example.com" in data)
		self.assertEqual(data["test_assign2@example.com"], 2)

		dontmanage.db.rollback()

	def test_assignment_removal(self):
		todo = dontmanage.get_doc({"doctype": "ToDo", "description": "test"}).insert()
		if not dontmanage.db.exists("User", "test@example.com"):
			dontmanage.get_doc({"doctype": "User", "email": "test@example.com", "first_name": "Test"}).insert()

		new_todo = assign(todo, "test@example.com")

		# remove assignment
		dontmanage.db.set_value("ToDo", new_todo[0].name, "allocated_to", "")

		self.assertFalse(get_assignments("ToDo", todo.name))


def assign(doc, user):
	return dontmanage.desk.form.assign_to.add(
		{
			"assign_to": [user],
			"doctype": doc.doctype,
			"name": doc.name,
			"description": "test",
		}
	)
