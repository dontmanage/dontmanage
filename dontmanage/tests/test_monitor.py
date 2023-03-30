# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
import dontmanage.monitor
from dontmanage.monitor import MONITOR_REDIS_KEY
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import set_request
from dontmanage.utils.response import build_response


class TestMonitor(DontManageTestCase):
	def setUp(self):
		dontmanage.conf.monitor = 1
		dontmanage.cache().delete_value(MONITOR_REDIS_KEY)

	def test_enable_monitor(self):
		set_request(method="GET", path="/api/method/dontmanage.ping")
		response = build_response("json")

		dontmanage.monitor.start()
		dontmanage.monitor.stop(response)

		logs = dontmanage.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)

		log = dontmanage.parse_json(logs[0].decode())
		self.assertTrue(log.duration)
		self.assertTrue(log.site)
		self.assertTrue(log.timestamp)
		self.assertTrue(log.uuid)
		self.assertTrue(log.request)
		self.assertEqual(log.transaction_type, "request")
		self.assertEqual(log.request["method"], "GET")

	def test_job(self):
		dontmanage.utils.background_jobs.execute_job(
			dontmanage.local.site, "dontmanage.ping", None, None, {}, is_async=False
		)

		logs = dontmanage.cache().lrange(MONITOR_REDIS_KEY, 0, -1)
		self.assertEqual(len(logs), 1)
		log = dontmanage.parse_json(logs[0].decode())
		self.assertEqual(log.transaction_type, "job")
		self.assertTrue(log.job)
		self.assertEqual(log.job["method"], "dontmanage.ping")
		self.assertEqual(log.job["scheduled"], False)
		self.assertEqual(log.job["wait"], 0)

	def test_flush(self):
		set_request(method="GET", path="/api/method/dontmanage.ping")
		response = build_response("json")
		dontmanage.monitor.start()
		dontmanage.monitor.stop(response)

		open(dontmanage.monitor.log_file(), "w").close()
		dontmanage.monitor.flush()

		with open(dontmanage.monitor.log_file()) as f:
			logs = f.readlines()

		self.assertEqual(len(logs), 1)
		log = dontmanage.parse_json(logs[0])
		self.assertEqual(log.transaction_type, "request")

	def tearDown(self):
		dontmanage.conf.monitor = 0
		dontmanage.cache().delete_value(MONITOR_REDIS_KEY)
