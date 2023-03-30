import dontmanage
from dontmanage.deferred_insert import deferred_insert, save_to_db
from dontmanage.tests.utils import DontManageTestCase


class TestDeferredInsert(DontManageTestCase):
	def test_deferred_insert(self):
		route_history = {"route": dontmanage.generate_hash(), "user": "Administrator"}
		deferred_insert("Route History", [route_history])

		save_to_db()
		self.assertTrue(dontmanage.db.exists("Route History", route_history))
