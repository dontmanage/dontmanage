# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import json

import dontmanage
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import set_request
from dontmanage.website.doctype.web_form.web_form import accept
from dontmanage.website.serve import get_response_content

test_dependencies = ["Web Form"]


class TestWebForm(DontManageTestCase):
	def setUp(self):
		dontmanage.conf.disable_website_cache = True

	def tearDown(self):
		dontmanage.conf.disable_website_cache = False

	def test_accept(self):
		dontmanage.set_user("Administrator")

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description",
			"starts_on": "2014-09-09",
		}

		accept(web_form="manage-events", data=json.dumps(doc))

		self.event_name = dontmanage.db.get_value("Event", {"subject": "_Test Event Web Form"})
		self.assertTrue(self.event_name)

	def test_edit(self):
		self.test_accept()

		doc = {
			"doctype": "Event",
			"subject": "_Test Event Web Form",
			"description": "_Test Event Description 1",
			"starts_on": "2014-09-09",
			"name": self.event_name,
		}

		self.assertNotEqual(
			dontmanage.db.get_value("Event", self.event_name, "description"), doc.get("description")
		)

		accept("manage-events", json.dumps(doc))

		self.assertEqual(dontmanage.db.get_value("Event", self.event_name, "description"), doc.get("description"))

	def test_webform_render(self):
		set_request(method="GET", path="manage-events/new")
		content = get_response_content("manage-events/new")
		self.assertIn('<h1 class="ellipsis">New Manage Events</h1>', content)
		self.assertIn('data-doctype="Web Form"', content)
		self.assertIn('data-path="manage-events/new"', content)
		self.assertIn('source-type="Generator"', content)

	def test_webform_html_meta_is_added(self):
		set_request(method="GET", path="manage-events/new")
		content = self.normalize_html(get_response_content("manage-events/new"))

		self.assertIn(self.normalize_html('<meta name="name" content="Test Meta Form Title">'), content)
		self.assertIn(
			self.normalize_html('<meta property="og:description" content="Test Meta Form Description">'),
			content,
		)
		self.assertIn(
			self.normalize_html('<meta property="og:image" content="https://dontmanage.io/files/dontmanage.png">'),
			content,
		)
