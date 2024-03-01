# Copyright (c) 2021, DontManage Technologies and Contributors
# See license.txt

import json
import os

import dontmanage
from dontmanage.tests.utils import DontManageTestCase


class TestPackage(DontManageTestCase):
	def test_package_release(self):
		make_test_package()
		make_test_module()
		make_test_doctype()
		make_test_server_script()
		make_test_web_page()

		# make release
		dontmanage.get_doc(dict(doctype="Package Release", package="Test Package", publish=1)).insert()

		self.assertTrue(os.path.exists(dontmanage.get_site_path("packages", "test-package")))
		self.assertTrue(
			os.path.exists(dontmanage.get_site_path("packages", "test-package", "test_module_for_package"))
		)
		self.assertTrue(
			os.path.exists(
				dontmanage.get_site_path(
					"packages",
					"test-package",
					"test_module_for_package",
					"doctype",
					"test_doctype_for_package",
				)
			)
		)
		with open(
			dontmanage.get_site_path(
				"packages",
				"test-package",
				"test_module_for_package",
				"doctype",
				"test_doctype_for_package",
				"test_doctype_for_package.json",
			)
		) as f:
			doctype = json.loads(f.read())
			self.assertEqual(doctype["doctype"], "DocType")
			self.assertEqual(doctype["name"], "Test DocType for Package")
			self.assertEqual(doctype["fields"][0]["fieldname"], "test_field")


def make_test_package():
	if not dontmanage.db.exists("Package", "Test Package"):
		dontmanage.get_doc(
			dict(doctype="Package", name="Test Package", package_name="test-package", readme="# Test Package")
		).insert()


def make_test_module():
	if not dontmanage.db.exists("Module Def", "Test Module for Package"):
		dontmanage.get_doc(
			dict(
				doctype="Module Def",
				module_name="Test Module for Package",
				custom=1,
				app_name="dontmanage",
				package="Test Package",
			)
		).insert()


def make_test_doctype():
	if not dontmanage.db.exists("DocType", "Test DocType for Package"):
		dontmanage.get_doc(
			dict(
				doctype="DocType",
				name="Test DocType for Package",
				custom=1,
				module="Test Module for Package",
				autoname="Prompt",
				fields=[dict(fieldname="test_field", fieldtype="Data", label="Test Field")],
			)
		).insert()


def make_test_server_script():
	if not dontmanage.db.exists("Server Script", "Test Script for Package"):
		dontmanage.get_doc(
			dict(
				doctype="Server Script",
				name="Test Script for Package",
				module="Test Module for Package",
				script_type="DocType Event",
				reference_doctype="Test DocType for Package",
				doctype_event="Before Save",
				script='dontmanage.msgprint("Test")',
			)
		).insert()


def make_test_web_page():
	if not dontmanage.db.exists("Web Page", "test-web-page-for-package"):
		dontmanage.get_doc(
			dict(
				doctype="Web Page",
				module="Test Module for Package",
				main_section="Some content",
				published=1,
				title="Test Web Page for Package",
			)
		).insert()
