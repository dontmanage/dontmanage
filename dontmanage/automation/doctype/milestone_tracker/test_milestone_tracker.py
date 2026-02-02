# Copyright (c) 2019, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import dontmanage
import dontmanage.cache_manager
from dontmanage.tests import IntegrationTestCase


class TestMilestoneTracker(IntegrationTestCase):
	def test_milestone(self):
		dontmanage.db.delete("Milestone Tracker")

		dontmanage.cache_manager.clear_doctype_map("Milestone Tracker")

		milestone_tracker = dontmanage.get_doc(
			doctype="Milestone Tracker", document_type="ToDo", track_field="status"
		).insert()

		todo = dontmanage.get_doc(doctype="ToDo", description="test milestone", status="Open").insert()

		milestones = dontmanage.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
		)

		self.assertEqual(len(milestones), 1)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Open")

		todo.status = "Closed"
		todo.save()

		milestones = dontmanage.get_all(
			"Milestone",
			fields=["track_field", "value", "milestone_tracker"],
			filters=dict(reference_type=todo.doctype, reference_name=todo.name),
			order_by="creation desc",
		)

		self.assertEqual(len(milestones), 2)
		self.assertEqual(milestones[0].track_field, "status")
		self.assertEqual(milestones[0].value, "Closed")

		# cleanup
		dontmanage.db.delete("Milestone")
		milestone_tracker.delete()
