# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import json

import dontmanage
from dontmanage.tests.utils import DontManageTestCase


class TestSeen(DontManageTestCase):
	def tearDown(self):
		dontmanage.set_user("Administrator")

	def test_if_user_is_added(self):
		ev = dontmanage.get_doc(
			{
				"doctype": "Event",
				"subject": "test event for seen",
				"starts_on": "2016-01-01 10:10:00",
				"event_type": "Public",
			}
		).insert()

		dontmanage.set_user("test@example.com")

		from dontmanage.desk.form.load import getdoc

		# load the form
		getdoc("Event", ev.name)

		# reload the event
		ev = dontmanage.get_doc("Event", ev.name)

		self.assertTrue("test@example.com" in json.loads(ev._seen))

		# test another user
		dontmanage.set_user("test1@example.com")

		# load the form
		getdoc("Event", ev.name)

		# reload the event
		ev = dontmanage.get_doc("Event", ev.name)

		self.assertTrue("test@example.com" in json.loads(ev._seen))
		self.assertTrue("test1@example.com" in json.loads(ev._seen))

		ev.save()
		ev = dontmanage.get_doc("Event", ev.name)

		self.assertFalse("test@example.com" in json.loads(ev._seen))
		self.assertTrue("test1@example.com" in json.loads(ev._seen))
