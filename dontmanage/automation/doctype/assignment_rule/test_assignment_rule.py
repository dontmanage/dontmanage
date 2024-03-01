# Copyright (c) 2021, DontManage Technologies and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.test_runner import make_test_records
from dontmanage.tests.utils import DontManageTestCase

TEST_DOCTYPE = "Assignment Test"


class TestAutoAssign(DontManageTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		dontmanage.db.delete("Assignment Rule")
		create_test_doctype(TEST_DOCTYPE)

	@classmethod
	def tearDownClass(cls):
		dontmanage.db.rollback()

	def setUp(self):
		dontmanage.set_user("Administrator")
		make_test_records("User")
		days = [
			dict(day="Sunday"),
			dict(day="Monday"),
			dict(day="Tuesday"),
			dict(day="Wednesday"),
			dict(day="Thursday"),
			dict(day="Friday"),
			dict(day="Saturday"),
		]
		self.days = days
		self.assignment_rule = get_assignment_rule([days, days])
		clear_assignments()

	def test_round_robin(self):
		# check if auto assigned to first user
		record = _make_test_record(public=1)
		self.assertEqual(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=record.name, status="Open"),
				"allocated_to",
			),
			"test@example.com",
		)

		# check if auto assigned to second user
		record = _make_test_record(public=1)
		self.assertEqual(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=record.name, status="Open"),
				"allocated_to",
			),
			"test1@example.com",
		)

		clear_assignments()

		# check if auto assigned to third user, even if
		# previous assignments where closed
		record = _make_test_record(public=1)
		self.assertEqual(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=record.name, status="Open"),
				"allocated_to",
			),
			"test2@example.com",
		)

		# check loop back to first user
		record = _make_test_record(public=1)
		self.assertEqual(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=record.name, status="Open"),
				"allocated_to",
			),
			"test@example.com",
		)

	def test_load_balancing(self):
		self.assignment_rule.rule = "Load Balancing"
		self.assignment_rule.save()

		for _ in range(30):
			_make_test_record(public=1)

		# check if each user has 10 assignments (?)
		for user in ("test@example.com", "test1@example.com", "test2@example.com"):
			self.assertEqual(
				len(dontmanage.get_all("ToDo", dict(allocated_to=user, reference_type=TEST_DOCTYPE))), 10
			)

		# clear 5 assignments for first user
		# can't do a limit in "delete" since postgres does not support it
		for d in dontmanage.get_all(
			"ToDo", dict(reference_type=TEST_DOCTYPE, allocated_to="test@example.com"), limit=5
		):
			dontmanage.db.delete("ToDo", {"name": d.name})

		# add 5 more assignments
		for _ in range(5):
			_make_test_record(public=1)

		# check if each user still has 10 assignments
		for user in ("test@example.com", "test1@example.com", "test2@example.com"):
			self.assertEqual(
				len(dontmanage.get_all("ToDo", dict(allocated_to=user, reference_type=TEST_DOCTYPE))), 10
			)

	def test_assingment_on_guest_submissions(self):
		"""Sometimes documents are inserted as guest, check if assignment rules run on them. Use case: Web Forms"""
		with self.set_user("Guest"):
			doc = _make_test_record(ignore_permissions=True, public=1)

		# check assignment to *anyone*
		self.assertTrue(
			dontmanage.db.get_value(
				"ToDo",
				{"reference_type": TEST_DOCTYPE, "reference_name": doc.name, "status": "Open"},
				"allocated_to",
			),
		)

	def test_based_on_field(self):
		self.assignment_rule.rule = "Based on Field"
		self.assignment_rule.field = "owner"
		self.assignment_rule.save()

		for test_user in ("test1@example.com", "test2@example.com"):
			dontmanage.set_user(test_user)
			note = _make_test_record(public=1)
			# check if auto assigned to doc owner, test1@example.com
			self.assertEqual(
				dontmanage.db.get_value(
					"ToDo",
					dict(reference_type=TEST_DOCTYPE, reference_name=note.name, status="Open"),
					"owner",
				),
				test_user,
			)

	def test_assign_condition(self):
		# check condition
		note = _make_test_record(public=0)

		self.assertEqual(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=note.name, status="Open"),
				"allocated_to",
			),
			None,
		)

	def test_clear_assignment(self):
		note = _make_test_record(public=1)

		# check if auto assigned to first user
		todo = dontmanage.get_list(
			"ToDo", dict(reference_type=TEST_DOCTYPE, reference_name=note.name, status="Open"), limit=1
		)[0]

		todo = dontmanage.get_doc("ToDo", todo["name"])
		self.assertEqual(todo.allocated_to, "test@example.com")

		# test auto unassign
		note.public = 0
		note.save()

		todo.load_from_db()

		# check if todo is cancelled
		self.assertEqual(todo.status, "Cancelled")

	def test_close_assignment(self):
		note = _make_test_record(public=1, content="valid")

		# check if auto assigned
		todo = dontmanage.get_list(
			"ToDo", dict(reference_type=TEST_DOCTYPE, reference_name=note.name, status="Open"), limit=1
		)[0]

		todo = dontmanage.get_doc("ToDo", todo["name"])
		self.assertEqual(todo.allocated_to, "test@example.com")

		note.content = "Closed"
		note.save()

		todo.load_from_db()

		# check if todo is closed
		self.assertEqual(todo.status, "Closed")
		# check if closed todo retained assignment
		self.assertEqual(todo.allocated_to, "test@example.com")

	def check_multiple_rules(self):
		note = _make_test_record(public=1, notify_on_login=1)

		# check if auto assigned to test3 (2nd rule is applied, as it has higher priority)
		self.assertEqual(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=note.name, status="Open"),
				"allocated_to",
			),
			"test@example.com",
		)

	def check_assignment_rule_scheduling(self):
		dontmanage.db.delete("Assignment Rule")

		days_1 = [dict(day="Sunday"), dict(day="Monday"), dict(day="Tuesday")]

		days_2 = [dict(day="Wednesday"), dict(day="Thursday"), dict(day="Friday"), dict(day="Saturday")]

		get_assignment_rule([days_1, days_2], ["public == 1", "public == 1"])

		dontmanage.flags.assignment_day = "Monday"
		note = _make_test_record(public=1)

		self.assertIn(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=note.name, status="Open"),
				"allocated_to",
			),
			["test@example.com", "test1@example.com", "test2@example.com"],
		)

		dontmanage.flags.assignment_day = "Friday"
		note = _make_test_record(public=1)

		self.assertIn(
			dontmanage.db.get_value(
				"ToDo",
				dict(reference_type=TEST_DOCTYPE, reference_name=note.name, status="Open"),
				"allocated_to",
			),
			["test3@example.com"],
		)

	def test_assignment_rule_condition(self):
		dontmanage.db.delete("Assignment Rule")

		assignment_rule = dontmanage.get_doc(
			dict(
				name="Assignment with Due Date",
				doctype="Assignment Rule",
				document_type=TEST_DOCTYPE,
				assign_condition="public == 0",
				due_date_based_on="expiry_date",
				assignment_days=self.days,
				users=[
					dict(user="test@example.com"),
				],
			)
		).insert()

		expiry_date = dontmanage.utils.add_days(dontmanage.utils.nowdate(), 2)
		note1 = _make_test_record(expiry_date=expiry_date)
		note2 = _make_test_record(expiry_date=expiry_date)

		note1_todo = dontmanage.get_all(
			"ToDo", filters=dict(reference_type=TEST_DOCTYPE, reference_name=note1.name, status="Open")
		)[0]

		note1_todo_doc = dontmanage.get_doc("ToDo", note1_todo.name)
		self.assertEqual(dontmanage.utils.get_date_str(note1_todo_doc.date), expiry_date)

		# due date should be updated if the reference doc's date is updated.
		note1.expiry_date = dontmanage.utils.add_days(expiry_date, 2)
		note1.save()
		note1_todo_doc.reload()
		self.assertEqual(dontmanage.utils.get_date_str(note1_todo_doc.date), note1.expiry_date)

		# saving one note's expiry should not update other note todo's due date
		note2_todo = dontmanage.get_all(
			"ToDo",
			filters=dict(reference_type=TEST_DOCTYPE, reference_name=note2.name, status="Open"),
			fields=["name", "date"],
		)[0]
		self.assertNotEqual(dontmanage.utils.get_date_str(note2_todo.date), note1.expiry_date)
		self.assertEqual(dontmanage.utils.get_date_str(note2_todo.date), expiry_date)
		assignment_rule.delete()
		dontmanage.db.commit()  # undo changes commited by DDL

	def test_submittable_assignment(self):
		# create a submittable doctype
		submittable_doctype = "Assignment Test Submittable"
		create_test_doctype(submittable_doctype)
		dt = dontmanage.get_doc("DocType", submittable_doctype)
		dt.is_submittable = 1
		dt.save()

		# create a rule for the submittable doctype
		assignment_rule = dontmanage.new_doc("Assignment Rule")
		assignment_rule.name = f"For {submittable_doctype}"
		assignment_rule.document_type = submittable_doctype
		assignment_rule.rule = "Round Robin"
		assignment_rule.extend("assignment_days", self.days)
		assignment_rule.append("users", {"user": "test@example.com"})
		assignment_rule.assign_condition = "docstatus == 1"
		assignment_rule.unassign_condition = "docstatus == 2"
		assignment_rule.save()

		# create a submittable doc
		doc = dontmanage.new_doc(submittable_doctype)
		doc.save()
		doc.submit()

		# check if todo is created
		todos = dontmanage.get_all(
			"ToDo",
			filters={
				"reference_type": submittable_doctype,
				"reference_name": doc.name,
				"status": "Open",
				"allocated_to": "test@example.com",
			},
		)
		self.assertEqual(len(todos), 1)

		# check if todo is closed on cancel
		doc.cancel()
		todos = dontmanage.get_all(
			"ToDo",
			filters={
				"reference_type": submittable_doctype,
				"reference_name": doc.name,
				"status": "Cancelled",
				"allocated_to": "test@example.com",
			},
		)
		self.assertEqual(len(todos), 1)


def clear_assignments():
	dontmanage.db.delete("ToDo", {"reference_type": TEST_DOCTYPE})


def get_assignment_rule(days, assign=None):
	dontmanage.delete_doc_if_exists("Assignment Rule", f"For {TEST_DOCTYPE} 1")

	if not assign:
		assign = ["public == 1", "notify_on_login == 1"]

	assignment_rule = dontmanage.get_doc(
		dict(
			name=f"For {TEST_DOCTYPE} 1",
			doctype="Assignment Rule",
			priority=0,
			document_type=TEST_DOCTYPE,
			assign_condition=assign[0],
			unassign_condition="public == 0 or notify_on_login == 1",
			close_condition='"Closed" in content',
			rule="Round Robin",
			assignment_days=days[0],
			users=[
				dict(user="test@example.com"),
				dict(user="test1@example.com"),
				dict(user="test2@example.com"),
			],
		)
	).insert()

	dontmanage.delete_doc_if_exists("Assignment Rule", f"For {TEST_DOCTYPE} 2")

	# 2nd rule
	dontmanage.get_doc(
		dict(
			name=f"For {TEST_DOCTYPE} 2",
			doctype="Assignment Rule",
			priority=1,
			document_type=TEST_DOCTYPE,
			assign_condition=assign[1],
			unassign_condition="notify_on_login == 0",
			rule="Round Robin",
			assignment_days=days[1],
			users=[dict(user="test3@example.com")],
		)
	).insert()

	return assignment_rule


def _make_test_record(
	*,
	ignore_permissions=False,
	**kwargs,
):
	doc = dontmanage.new_doc(TEST_DOCTYPE)

	if kwargs:
		doc.update(kwargs)

	return doc.insert(ignore_permissions=ignore_permissions)


def create_test_doctype(doctype: str):
	"""Create custom doctype."""
	dontmanage.delete_doc("DocType", doctype)

	dontmanage.get_doc(
		{
			"doctype": "DocType",
			"name": doctype,
			"module": "Custom",
			"custom": 1,
			"fields": [
				{
					"fieldname": "expiry_date",
					"label": "Expiry Date",
					"fieldtype": "Date",
				},
				{
					"fieldname": "notify_on_login",
					"label": "Notify on Login",
					"fieldtype": "Check",
				},
				{
					"fieldname": "public",
					"label": "Public",
					"fieldtype": "Check",
				},
				{
					"fieldname": "content",
					"label": "Content",
					"fieldtype": "Text",
				},
			],
			"permissions": [
				{
					"create": 1,
					"delete": 1,
					"email": 1,
					"export": 1,
					"print": 1,
					"read": 1,
					"report": 1,
					"role": "All",
					"share": 1,
					"write": 1,
				},
			],
		}
	).insert()
