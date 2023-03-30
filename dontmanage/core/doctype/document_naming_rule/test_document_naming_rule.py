# Copyright (c) 2020, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.tests.utils import DontManageTestCase


class TestDocumentNamingRule(DontManageTestCase):
	def test_naming_rule_by_series(self):
		naming_rule = dontmanage.get_doc(
			dict(doctype="Document Naming Rule", document_type="ToDo", prefix="test-todo-", prefix_digits=5)
		).insert()

		todo = dontmanage.get_doc(
			dict(doctype="ToDo", description="Is this my name " + dontmanage.generate_hash())
		).insert()

		self.assertEqual(todo.name, "test-todo-00001")

		naming_rule.delete()
		todo.delete()

	def test_naming_rule_by_condition(self):
		naming_rule = dontmanage.get_doc(
			dict(
				doctype="Document Naming Rule",
				document_type="ToDo",
				prefix="test-high-",
				prefix_digits=5,
				priority=10,
				conditions=[dict(field="priority", condition="=", value="High")],
			)
		).insert()

		# another rule
		naming_rule_1 = dontmanage.copy_doc(naming_rule)
		naming_rule_1.prefix = "test-medium-"
		naming_rule_1.conditions[0].value = "Medium"
		naming_rule_1.insert()

		# default rule with low priority - should not get applied for rules
		# with higher priority
		naming_rule_2 = dontmanage.copy_doc(naming_rule)
		naming_rule_2.prefix = "test-low-"
		naming_rule_2.priority = 0
		naming_rule_2.conditions = []
		naming_rule_2.insert()

		todo = dontmanage.get_doc(
			dict(doctype="ToDo", priority="High", description="Is this my name " + dontmanage.generate_hash())
		).insert()

		todo_1 = dontmanage.get_doc(
			dict(doctype="ToDo", priority="Medium", description="Is this my name " + dontmanage.generate_hash())
		).insert()

		todo_2 = dontmanage.get_doc(
			dict(doctype="ToDo", priority="Low", description="Is this my name " + dontmanage.generate_hash())
		).insert()

		try:
			self.assertEqual(todo.name, "test-high-00001")
			self.assertEqual(todo_1.name, "test-medium-00001")
			self.assertEqual(todo_2.name, "test-low-00001")
		finally:
			naming_rule.delete()
			naming_rule_1.delete()
			naming_rule_2.delete()
			todo.delete()
			todo_1.delete()
			todo_2.delete()
