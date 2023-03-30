# Copyright (c) 2022, DontManage Technologies and Contributors
# See license.txt

import dontmanage
from dontmanage.core.doctype.rq_worker.rq_worker import RQWorker
from dontmanage.tests.utils import DontManageTestCase


class TestRQWorker(DontManageTestCase):
	def test_get_worker_list(self):
		workers = RQWorker.get_list({})
		self.assertGreaterEqual(len(workers), 1)
		self.assertTrue(any("short" in w.queue_type for w in workers))

	def test_worker_serialization(self):
		workers = RQWorker.get_list({})
		dontmanage.get_doc("RQ Worker", workers[0].pid)
