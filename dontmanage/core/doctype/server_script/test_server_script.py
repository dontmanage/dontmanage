# Copyright (c) 2019, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import requests

import dontmanage
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import get_site_url

scripts = [
	dict(
		name="test_todo",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "test" in doc.description:
	doc.status = 'Closed'
""",
	),
	dict(
		name="test_todo_validate",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="ToDo",
		script="""
if "validate" in doc.description:
	raise dontmanage.ValidationError
""",
	),
	dict(
		name="test_api",
		script_type="API",
		api_method="test_server_script",
		allow_guest=1,
		script="""
dontmanage.response['message'] = 'hello'
""",
	),
	dict(
		name="test_return_value",
		script_type="API",
		api_method="test_return_value",
		allow_guest=1,
		script="""
dontmanage.flags = 'hello'
""",
	),
	dict(
		name="test_permission_query",
		script_type="Permission Query",
		reference_doctype="ToDo",
		script="""
conditions = '1 = 1'
""",
	),
	dict(
		name="test_invalid_namespace_method",
		script_type="DocType Event",
		doctype_event="Before Insert",
		reference_doctype="Note",
		script="""
dontmanage.method_that_doesnt_exist("do some magic")
""",
	),
	dict(
		name="test_todo_commit",
		script_type="DocType Event",
		doctype_event="Before Save",
		reference_doctype="ToDo",
		disabled=1,
		script="""
dontmanage.db.commit()
""",
	),
	dict(
		name="test_add_index",
		script_type="DocType Event",
		doctype_event="Before Save",
		reference_doctype="ToDo",
		disabled=1,
		script="""
dontmanage.db.add_index("Todo", ["color", "date"])
""",
	),
]


class TestServerScript(DontManageTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		dontmanage.db.truncate("Server Script")
		dontmanage.get_doc("User", "Administrator").add_roles("Script Manager")
		for script in scripts:
			script_doc = dontmanage.get_doc(doctype="Server Script")
			script_doc.update(script)
			script_doc.insert()

		dontmanage.db.commit()

	@classmethod
	def tearDownClass(cls):
		dontmanage.db.commit()
		dontmanage.db.truncate("Server Script")
		dontmanage.cache().delete_value("server_script_map")

	def setUp(self):
		dontmanage.cache().delete_value("server_script_map")

	def test_doctype_event(self):
		todo = dontmanage.get_doc(dict(doctype="ToDo", description="hello")).insert()
		self.assertEqual(todo.status, "Open")

		todo = dontmanage.get_doc(dict(doctype="ToDo", description="test todo")).insert()
		self.assertEqual(todo.status, "Closed")

		self.assertRaises(
			dontmanage.ValidationError, dontmanage.get_doc(dict(doctype="ToDo", description="validate me")).insert
		)

	def test_api(self):
		response = requests.post(get_site_url(dontmanage.local.site) + "/api/method/test_server_script")
		self.assertEqual(response.status_code, 200)
		self.assertEqual("hello", response.json()["message"])

	def test_api_return(self):
		self.assertEqual(dontmanage.get_doc("Server Script", "test_return_value").execute_method(), "hello")

	def test_permission_query(self):
		if dontmanage.conf.db_type == "mariadb":
			self.assertTrue("where (1 = 1)" in dontmanage.db.get_list("ToDo", run=False))
		else:
			self.assertTrue("where (1 = '1')" in dontmanage.db.get_list("ToDo", run=False))
		self.assertTrue(isinstance(dontmanage.db.get_list("ToDo"), list))

	def test_attribute_error(self):
		"""Raise AttributeError if method not found in Namespace"""
		note = dontmanage.get_doc({"doctype": "Note", "title": "Test Note: Server Script"})
		self.assertRaises(AttributeError, note.insert)

	def test_syntax_validation(self):
		server_script = scripts[0]
		server_script["script"] = "js || code.?"

		with self.assertRaises(dontmanage.ValidationError) as se:
			dontmanage.get_doc(doctype="Server Script", **server_script).insert()

		self.assertTrue(
			"invalid python code" in str(se.exception).lower(), msg="Python code validation not working"
		)

	def test_commit_in_doctype_event(self):
		server_script = dontmanage.get_doc("Server Script", "test_todo_commit")
		server_script.disabled = 0
		server_script.save()

		self.assertRaises(
			AttributeError, dontmanage.get_doc(dict(doctype="ToDo", description="test me")).insert
		)

		server_script.disabled = 1
		server_script.save()

	def test_add_index_in_doctype_event(self):
		server_script = dontmanage.get_doc("Server Script", "test_add_index")
		server_script.disabled = 0
		server_script.save()

		self.assertRaises(
			AttributeError, dontmanage.get_doc(dict(doctype="ToDo", description="test me")).insert
		)

		server_script.disabled = 1
		server_script.save()

	def test_restricted_qb(self):
		todo = dontmanage.get_doc(doctype="ToDo", description="QbScriptTestNote")
		todo.insert()

		script = dontmanage.get_doc(
			doctype="Server Script",
			name="test_qb_restrictions",
			script_type="API",
			api_method="test_qb_restrictions",
			allow_guest=1,
			# whitelisted update
			script=f"""
dontmanage.db.set_value("ToDo", "{todo.name}", "description", "safe")
""",
		)
		script.insert()
		script.execute_method()

		todo.reload()
		self.assertEqual(todo.description, "safe")

		# unsafe update
		script.script = f"""
todo = dontmanage.qb.DocType("ToDo")
dontmanage.qb.update(todo).set(todo.description, "unsafe").where(todo.name == "{todo.name}").run()
"""
		script.save()
		self.assertRaises(dontmanage.PermissionError, script.execute_method)
		todo.reload()
		self.assertEqual(todo.description, "safe")

		# safe select
		script.script = f"""
todo = dontmanage.qb.DocType("ToDo")
dontmanage.qb.from_(todo).select(todo.name).where(todo.name == "{todo.name}").run()
"""
		script.save()
		script.execute_method()

	def test_scripts_all_the_way_down(self):
		# why not
		script = dontmanage.get_doc(
			doctype="Server Script",
			name="test_nested_scripts_1",
			script_type="API",
			api_method="test_nested_scripts_1",
			script=f"""log("nothing")""",
		)
		script.insert()
		script.execute_method()

		script = dontmanage.get_doc(
			doctype="Server Script",
			name="test_nested_scripts_2",
			script_type="API",
			api_method="test_nested_scripts_2",
			script=f"""dontmanage.call("test_nested_scripts_1")""",
		)
		script.insert()
		script.execute_method()
