# Copyright (c) 2019, DontManage and Contributors
# License: MIT. See LICENSE

import sqlparse

import dontmanage
import dontmanage.recorder
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import set_request
from dontmanage.website.serve import get_response_content


class TestRecorder(DontManageTestCase):
	def setUp(self):
		dontmanage.recorder.stop()
		dontmanage.recorder.delete()
		set_request()
		dontmanage.recorder.start()
		dontmanage.recorder.record()

	def test_start(self):
		dontmanage.recorder.dump()
		requests = dontmanage.recorder.get()
		self.assertEqual(len(requests), 1)

	def test_do_not_record(self):
		dontmanage.recorder.do_not_record(dontmanage.get_all)("DocType")
		dontmanage.recorder.dump()
		requests = dontmanage.recorder.get()
		self.assertEqual(len(requests), 0)

	def test_get(self):
		dontmanage.recorder.dump()

		requests = dontmanage.recorder.get()
		self.assertEqual(len(requests), 1)

		request = dontmanage.recorder.get(requests[0]["uuid"])
		self.assertTrue(request)

	def test_delete(self):
		dontmanage.recorder.dump()

		requests = dontmanage.recorder.get()
		self.assertEqual(len(requests), 1)

		dontmanage.recorder.delete()

		requests = dontmanage.recorder.get()
		self.assertEqual(len(requests), 0)

	def test_record_without_sql_queries(self):
		dontmanage.recorder.dump()

		requests = dontmanage.recorder.get()
		request = dontmanage.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"]), 0)

	def test_record_with_sql_queries(self):
		dontmanage.get_all("DocType")
		dontmanage.recorder.dump()

		requests = dontmanage.recorder.get()
		request = dontmanage.recorder.get(requests[0]["uuid"])

		self.assertNotEqual(len(request["calls"]), 0)

	def test_explain(self):
		dontmanage.db.sql("SELECT * FROM tabDocType")
		dontmanage.db.sql("COMMIT")
		dontmanage.recorder.dump()

		requests = dontmanage.recorder.get()
		request = dontmanage.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"][0]["explain_result"]), 1)
		self.assertEqual(len(request["calls"][1]["explain_result"]), 0)

	def test_multiple_queries(self):
		queries = [
			{"mariadb": "SELECT * FROM tabDocType", "postgres": 'SELECT * FROM "tabDocType"'},
			{"mariadb": "SELECT COUNT(*) FROM tabDocType", "postgres": 'SELECT COUNT(*) FROM "tabDocType"'},
			{"mariadb": "COMMIT", "postgres": "COMMIT"},
		]

		sql_dialect = dontmanage.db.db_type or "mariadb"
		for query in queries:
			dontmanage.db.sql(query[sql_dialect])

		dontmanage.recorder.dump()

		requests = dontmanage.recorder.get()
		request = dontmanage.recorder.get(requests[0]["uuid"])

		self.assertEqual(len(request["calls"]), len(queries))

		for query, call in zip(queries, request["calls"]):
			self.assertEqual(
				call["query"], sqlparse.format(query[sql_dialect].strip(), keyword_case="upper", reindent=True)
			)

	def test_duplicate_queries(self):
		queries = [
			("SELECT * FROM tabDocType", 2),
			("SELECT COUNT(*) FROM tabDocType", 1),
			("select * from tabDocType", 2),
			("COMMIT", 3),
			("COMMIT", 3),
			("COMMIT", 3),
		]
		for query in queries:
			dontmanage.db.sql(query[0])

		dontmanage.recorder.dump()

		requests = dontmanage.recorder.get()
		request = dontmanage.recorder.get(requests[0]["uuid"])

		for query, call in zip(queries, request["calls"]):
			self.assertEqual(call["exact_copies"], query[1])

	def test_error_page_rendering(self):
		content = get_response_content("error")
		self.assertIn("Error", content)


class TestRecorderDeco(DontManageTestCase):
	def test_recorder_flag(self):
		dontmanage.recorder.delete()

		@dontmanage.recorder.record_queries
		def test():
			dontmanage.get_all("User")

		test()
		self.assertTrue(dontmanage.recorder.get())
