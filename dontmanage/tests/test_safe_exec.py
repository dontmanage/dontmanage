import types

import dontmanage
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils.safe_exec import get_safe_globals, safe_exec


class TestSafeExec(DontManageTestCase):
	def test_import_fails(self):
		self.assertRaises(ImportError, safe_exec, "import os")

	def test_internal_attributes(self):
		self.assertRaises(SyntaxError, safe_exec, "().__class__.__call__")

	def test_utils(self):
		_locals = dict(out=None)
		safe_exec("""out = dontmanage.utils.cint("1")""", None, _locals)
		self.assertEqual(_locals["out"], 1)

	def test_safe_eval(self):
		self.assertEqual(dontmanage.safe_eval("1+1"), 2)
		self.assertRaises(AttributeError, dontmanage.safe_eval, "dontmanage.utils.os.path", get_safe_globals())

	def test_sql(self):
		_locals = dict(out=None)
		safe_exec(
			"""out = dontmanage.db.sql("select name from tabDocType where name='DocType'")""", None, _locals
		)
		self.assertEqual(_locals["out"][0][0], "DocType")

		self.assertRaises(
			dontmanage.PermissionError, safe_exec, 'dontmanage.db.sql("update tabToDo set description=NULL")'
		)

	def test_query_builder(self):
		_locals = dict(out=None)
		safe_exec(
			script="""out = dontmanage.qb.from_("User").select(dontmanage.qb.terms.PseudoColumn("Max(name)")).run()""",
			_globals=None,
			_locals=_locals,
		)
		self.assertEqual(dontmanage.db.sql("SELECT Max(name) FROM tabUser"), _locals["out"])

	def test_safe_query_builder(self):
		self.assertRaises(
			dontmanage.PermissionError, safe_exec, """dontmanage.qb.from_("User").delete().run()"""
		)

	def test_call(self):
		# call non whitelisted method
		self.assertRaises(dontmanage.PermissionError, safe_exec, """dontmanage.call("dontmanage.get_user")""")

		# call whitelisted method
		safe_exec("""dontmanage.call("ping")""")

	def test_enqueue(self):
		# enqueue non whitelisted method
		self.assertRaises(
			dontmanage.PermissionError, safe_exec, """dontmanage.enqueue("dontmanage.get_user", now=True)"""
		)

		# enqueue whitelisted method
		safe_exec("""dontmanage.enqueue("ping", now=True)""")

	def test_ensure_getattrable_globals(self):
		def check_safe(objects):
			for obj in objects:
				if isinstance(obj, (types.ModuleType, types.CodeType, types.TracebackType, types.FrameType)):
					self.fail(f"{obj} wont work in safe exec.")
				elif isinstance(obj, dict):
					check_safe(obj.values())

		check_safe(get_safe_globals().values())

	def test_unsafe_objects(self):
		unsafe_global = {"dontmanage": dontmanage}
		self.assertRaises(SyntaxError, safe_exec, """dontmanage.msgprint("Hello")""", unsafe_global)
