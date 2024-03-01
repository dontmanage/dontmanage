import os
import shutil
import unittest

import dontmanage
from dontmanage import scrub
from dontmanage.core.doctype.doctype.test_doctype import new_doctype
from dontmanage.custom.doctype.custom_field.custom_field import create_custom_field
from dontmanage.model.meta import trim_table
from dontmanage.modules import export_customizations, export_module_json, get_module_path
from dontmanage.modules.utils import export_doc, sync_customizations
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import now_datetime


def write_file(path, content):
	with open(path, "w") as f:
		f.write(content)


def delete_file(path):
	if path:
		os.remove(path)


def delete_path(path):
	if path:
		shutil.rmtree(path, ignore_errors=True)


class TestUtils(DontManageTestCase):
	def setUp(self):
		self._dev_mode = dontmanage.local.conf.developer_mode
		self._in_import = dontmanage.local.flags.in_import

		dontmanage.local.conf.developer_mode = True

		if self._testMethodName == "test_export_module_json_no_export":
			dontmanage.local.flags.in_import = True

		if self._testMethodName in ("test_export_customizations", "test_sync_customizations"):
			df = {
				"fieldname": "test_export_customizations_field",
				"label": "Custom Data Field",
				"fieldtype": "Data",
			}
			self.custom_field = create_custom_field("Note", df=df)

		if self._testMethodName == "test_export_doc":
			self.note = dontmanage.new_doc("Note")
			self.note.title = dontmanage.generate_hash(length=10)
			self.note.save()

		if self._testMethodName == "test_make_boilerplate":
			self.doctype = new_doctype("Test DocType Boilerplate")
			self.doctype.insert()

	def tearDown(self):
		dontmanage.local.conf.developer_mode = self._dev_mode
		dontmanage.local.flags.in_import = self._in_import

		if self._testMethodName in ("test_export_customizations", "test_sync_customizations"):
			self.custom_field.delete()
			trim_table("Note", dry_run=False)
			delattr(self, "custom_field")
			delete_path(dontmanage.get_module_path("Desk", "Note"))

		if self._testMethodName == "test_export_doc":
			self.note.delete()
			delattr(self, "note")

		if self._testMethodName == "test_make_boilerplate":
			self.doctype.delete(force=True)
			scrubbed = dontmanage.scrub(self.doctype.name)
			self.addCleanup(
				delete_path,
				path=dontmanage.get_app_path("dontmanage", "core", "doctype", scrubbed),
			)
			dontmanage.db.sql_ddl("DROP TABLE `tabTest DocType Boilerplate`")
			delattr(self, "doctype")

	def test_export_module_json_no_export(self):
		doc = dontmanage.get_last_doc("DocType")
		self.assertIsNone(export_module_json(doc=doc, is_standard=True, module=doc.module))

	@unittest.skipUnless(
		os.access(dontmanage.get_app_path("dontmanage"), os.W_OK), "Only run if dontmanage app paths is writable"
	)
	def test_export_module_json(self):
		doc = dontmanage.get_last_doc("DocType", {"issingle": 0, "custom": 0})
		export_doc_path = os.path.join(
			get_module_path(doc.module),
			scrub(doc.doctype),
			scrub(doc.name),
			f"{scrub(doc.name)}.json",
		)
		with open(export_doc_path) as f:
			export_doc_before = dontmanage.parse_json(f.read())

		last_modified_before = os.path.getmtime(export_doc_path)
		self.addCleanup(write_file, path=export_doc_path, content=dontmanage.as_json(export_doc_before))

		dontmanage.flags.in_import = False
		dontmanage.conf.developer_mode = True
		export_path = export_module_json(doc=doc, is_standard=True, module=doc.module)

		last_modified_after = os.path.getmtime(export_doc_path)

		with open(f"{export_path}.json") as f:
			dontmanage.parse_json(f.read())  # export_doc_after

		self.assertTrue(last_modified_after > last_modified_before)

	@unittest.skipUnless(
		os.access(dontmanage.get_app_path("dontmanage"), os.W_OK), "Only run if dontmanage app paths is writable"
	)
	def test_export_customizations(self):
		file_path = export_customizations(module="Custom", doctype="Note")
		self.addCleanup(delete_file, path=file_path)
		self.assertTrue(file_path.endswith("/custom/custom/note.json"))
		self.assertTrue(os.path.exists(file_path))

	@unittest.skipUnless(
		os.access(dontmanage.get_app_path("dontmanage"), os.W_OK), "Only run if dontmanage app paths is writable"
	)
	def test_sync_customizations(self):
		custom_field = dontmanage.get_doc(
			"Custom Field", {"dt": "Note", "fieldname": "test_export_customizations_field"}
		)

		file_path = export_customizations(module="Custom", doctype="Note", sync_on_migrate=True)
		custom_field.db_set("modified", now_datetime())
		custom_field.reload()

		self.assertTrue(file_path.endswith("/custom/custom/note.json"))
		self.assertTrue(os.path.exists(file_path))
		last_modified_before = custom_field.modified

		sync_customizations(app="dontmanage")

		self.assertTrue(file_path.endswith("/custom/custom/note.json"))
		self.assertTrue(os.path.exists(file_path))
		custom_field.reload()
		last_modified_after = custom_field.modified

		self.assertNotEqual(last_modified_after, last_modified_before)
		self.addCleanup(delete_file, path=file_path)

	def test_reload_doc(self):
		dontmanage.db.set_value("DocType", "Note", "migration_hash", "", update_modified=False)
		self.assertFalse(dontmanage.db.get_value("DocType", "Note", "migration_hash"))
		dontmanage.db.set_value(
			"DocField",
			{"parent": "Note", "fieldname": "title"},
			"fieldtype",
			"Text",
			update_modified=False,
		)
		self.assertEqual(
			dontmanage.db.get_value("DocField", {"parent": "Note", "fieldname": "title"}, "fieldtype"),
			"Text",
		)
		dontmanage.reload_doctype("Note")
		self.assertEqual(
			dontmanage.db.get_value("DocField", {"parent": "Note", "fieldname": "title"}, "fieldtype"),
			"Data",
		)
		self.assertTrue(dontmanage.db.get_value("DocType", "Note", "migration_hash"))

	@unittest.skipUnless(
		os.access(dontmanage.get_app_path("dontmanage"), os.W_OK), "Only run if dontmanage app paths is writable"
	)
	def test_export_doc(self):
		exported_doc_path = dontmanage.get_app_path(
			"dontmanage", "desk", "note", self.note.name, f"{self.note.name}.json"
		)
		folder_path = os.path.abspath(os.path.dirname(exported_doc_path))
		export_doc(doctype="Note", name=self.note.name)
		self.addCleanup(delete_path, path=folder_path)
		self.assertTrue(os.path.exists(exported_doc_path))

	@unittest.skipUnless(
		os.access(dontmanage.get_app_path("dontmanage"), os.W_OK), "Only run if dontmanage app paths is writable"
	)
	def test_make_boilerplate(self):
		scrubbed = dontmanage.scrub(self.doctype.name)
		self.assertFalse(
			os.path.exists(dontmanage.get_app_path("dontmanage", "core", "doctype", scrubbed, f"{scrubbed}.json"))
		)
		self.doctype.custom = False
		self.doctype.save()
		self.assertTrue(
			os.path.exists(dontmanage.get_app_path("dontmanage", "core", "doctype", scrubbed, f"{scrubbed}.json"))
		)
