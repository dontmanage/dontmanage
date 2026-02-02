import dontmanage
from dontmanage.model.sync import remove_orphan_entities
from dontmanage.modules.export_file import delete_folder
from dontmanage.tests import IntegrationTestCase


class TestRemovingOrphans(IntegrationTestCase):
	def test_removing_orphan(self):
		_before = dontmanage.conf.developer_mode
		dontmanage.conf.developer_mode = True
		# Create a new report
		report = dontmanage.new_doc("Report")
		args = {
			"doctype": "Report",
			"report_name": "Orphan Report",
			"ref_doctype": "DocType",
			"is_standard": "Yes",
			"module": "Custom",
		}
		report.update(args)
		report.save()
		print(f"Created report: {report.name}")
		# delete only fixture (emulating that the export/entity is deleted by the developer)
		delete_folder("Custom", "Report", report.name)
		self.assertTrue(dontmanage.db.exists("Report", report.name))
		if dontmanage.db.exists("Report", report.name):
			remove_orphan_entities()
		self.assertFalse(dontmanage.db.exists("Report", report.name))
		dontmanage.conf.developer_mode = _before
