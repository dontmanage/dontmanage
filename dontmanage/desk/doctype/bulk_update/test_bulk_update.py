# Copyright (c) 2023, DontManage Technologies and Contributors
# See LICENSE

import time

import dontmanage
from dontmanage.core.doctype.doctype.test_doctype import new_doctype
from dontmanage.desk.doctype.bulk_update.bulk_update import submit_cancel_or_update_docs
from dontmanage.tests.utils import DontManageTestCase, timeout


class TestBulkUpdate(DontManageTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		cls.doctype = new_doctype(is_submittable=1, custom=1).insert().name
		dontmanage.db.commit()
		for _ in range(50):
			dontmanage.new_doc(cls.doctype, some_fieldname=dontmanage.mock("name")).insert()

	@timeout()
	def wait_for_assertion(self, assertion):
		"""Wait till an assertion becomes True"""
		while True:
			if assertion():
				break
			time.sleep(0.2)

	def test_bulk_submit_in_background(self):
		unsubmitted = dontmanage.get_all(self.doctype, {"docstatus": 0}, limit=5, pluck="name")
		failed = submit_cancel_or_update_docs(self.doctype, unsubmitted, action="submit")
		self.assertEqual(failed, [])

		def check_docstatus(docs, status):
			dontmanage.db.rollback()
			matching_docs = dontmanage.get_all(
				self.doctype, {"docstatus": status, "name": ("in", docs)}, pluck="name"
			)
			return set(matching_docs) == set(docs)

		unsubmitted = dontmanage.get_all(self.doctype, {"docstatus": 0}, limit=20, pluck="name")
		submit_cancel_or_update_docs(self.doctype, unsubmitted, action="submit")

		self.wait_for_assertion(lambda: check_docstatus(unsubmitted, 1))

		submitted = dontmanage.get_all(self.doctype, {"docstatus": 1}, limit=20, pluck="name")
		submit_cancel_or_update_docs(self.doctype, submitted, action="cancel")
		self.wait_for_assertion(lambda: check_docstatus(submitted, 2))
