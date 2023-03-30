import json
import os
from unittest.mock import patch

import dontmanage
import dontmanage.modules.utils
from dontmanage.core.doctype.doctype.test_doctype import new_doctype
from dontmanage.desk.form.save import savedocs
from dontmanage.model.document import Document
from dontmanage.tests.utils import DontManageTestCase

TEST_DOCTYPE_NAME = "VirtualDoctypeTest"


class VirtualDoctypeTest(Document):
	"""This is a virtual doctype controller for test/demo purposes.

	- It uses a JSON file on disk as "backend".
	- Key is docname and value is the document itself.

	Example:
	{
	        "doc1": {"name": "doc1", ...}
	        "doc2": {"name": "doc2", ...}
	}
	"""

	DATA_FILE = "data_file.json"

	@staticmethod
	def get_current_data() -> dict[str, dict]:
		"""Read data from disk"""
		if not os.path.exists(VirtualDoctypeTest.DATA_FILE):
			return {}

		with open(VirtualDoctypeTest.DATA_FILE) as f:
			return json.load(f)

	@staticmethod
	def update_data(data: dict[str, dict]) -> None:
		"""Flush updated data to disk"""
		with open(VirtualDoctypeTest.DATA_FILE, "w+") as data_file:
			json.dump(data, data_file)

	def db_insert(self, *args, **kwargs):
		d = self.get_valid_dict(convert_dates_to_str=True)

		data = self.get_current_data()
		data[d.name] = d

		self.update_data(data)

	def load_from_db(self):
		data = self.get_current_data()
		d = data.get(self.name)
		super(Document, self).__init__(d)

	def db_update(self, *args, **kwargs):
		# For this example insert and update are same operation,
		# it might be  different for you
		self.db_insert(*args, **kwargs)

	def delete(self):
		data = self.get_current_data()
		data.pop(self.name, None)
		self.update_data(data)

	@staticmethod
	def get_list(args):
		data = VirtualDoctypeTest.get_current_data()
		return [dontmanage._dict(doc) for name, doc in data.items()]

	@staticmethod
	def get_count(args):
		data = VirtualDoctypeTest.get_current_data()
		return len(data)

	@staticmethod
	def get_stats(args):
		return {}


class TestVirtualDoctypes(DontManageTestCase):
	@classmethod
	def setUpClass(cls):
		dontmanage.flags.allow_doctype_export = True
		cls.addClassCleanup(dontmanage.flags.pop, "allow_doctype_export", None)

		vdt = new_doctype(name=TEST_DOCTYPE_NAME, is_virtual=1, custom=0).insert()
		cls.addClassCleanup(vdt.delete)

		patch_virtual_doc = patch(
			"dontmanage.controllers", new={dontmanage.local.site: {TEST_DOCTYPE_NAME: VirtualDoctypeTest}}
		)
		patch_virtual_doc.start()
		cls.addClassCleanup(patch_virtual_doc.stop)

	def tearDown(self):
		if os.path.exists(VirtualDoctypeTest.DATA_FILE):
			os.remove(VirtualDoctypeTest.DATA_FILE)

	def test_insert_update_and_load_from_desk(self):
		"""Insert, update, reload and assert changes"""

		dontmanage.response.docs = []
		doc = json.dumps(
			{
				"docstatus": 0,
				"doctype": TEST_DOCTYPE_NAME,
				"name": "new-doctype-1",
				"__islocal": 1,
				"__unsaved": 1,
				"owner": "Administrator",
				TEST_DOCTYPE_NAME: "Original Data",
			}
		)
		savedocs(doc, "Save")

		docname = dontmanage.response.docs[0]["name"]

		doc = dontmanage.get_doc(TEST_DOCTYPE_NAME, docname)
		doc.some_fieldname = "New Data"

		savedocs(doc.as_json(), "Save")

		doc.reload()
		self.assertEqual(doc.some_fieldname, "New Data")

	def test_multiple_doc_insert_and_get_list(self):
		doc1 = dontmanage.get_doc(doctype=TEST_DOCTYPE_NAME, some_fieldname="first").insert()
		doc2 = dontmanage.get_doc(doctype=TEST_DOCTYPE_NAME, some_fieldname="second").insert()

		docs = {doc1.name, doc2.name}

		doc2.reload()
		doc1.reload()
		updated_docs = {doc1.name, doc2.name}
		self.assertEqual(docs, updated_docs)

		listed_docs = {d.name for d in VirtualDoctypeTest.get_list({})}
		self.assertEqual(docs, listed_docs)

	def test_get_count(self):
		args = {"doctype": TEST_DOCTYPE_NAME, "filters": [], "fields": []}
		self.assertIsInstance(VirtualDoctypeTest.get_count(args), int)

	def test_delete_doc(self):
		doc = dontmanage.get_doc(doctype=TEST_DOCTYPE_NAME, some_fieldname="data").insert()

		dontmanage.delete_doc(doc.doctype, doc.name)

		listed_docs = {d.name for d in VirtualDoctypeTest.get_list({})}
		self.assertNotIn(doc.name, listed_docs)
