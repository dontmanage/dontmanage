import dontmanage
from dontmanage.tests import IntegrationTestCase
from dontmanage.utils import set_request
from dontmanage.website.serve import get_response
from dontmanage.www.list import get_list_context


class TestWebform(IntegrationTestCase):
	def test_webform_publish_functionality(self):
		request_data = dontmanage.get_doc("Web Form", "request-data")
		# publish webform
		request_data.published = True
		request_data.save()
		set_request(method="GET", path="request-data/new")
		response = get_response()
		self.assertEqual(response.status_code, 200)

		# un-publish webform
		request_data.published = False
		request_data.save()
		response = get_response()
		self.assertEqual(response.status_code, 404)


def create_custom_doctype():
	dontmanage.get_doc(
		{
			"doctype": "DocType",
			"name": "Custom Doctype",
			"module": "Core",
			"custom": 1,
			"fields": [{"label": "Title", "fieldname": "title", "fieldtype": "Data"}],
		}
	).insert(ignore_if_duplicate=True)


def create_webform():
	dontmanage.get_doc(
		{
			"doctype": "Web Form",
			"module": "Core",
			"title": "Test Webform",
			"route": "test-webform",
			"doc_type": "Custom Doctype",
			"web_form_fields": [
				{
					"doctype": "Web Form Field",
					"fieldname": "title",
					"fieldtype": "Data",
					"label": "Title",
				}
			],
		}
	).insert(ignore_if_duplicate=True)


def set_webform_hook(key, value):
	from dontmanage import hooks

	# reset hooks
	for hook in "webform_list_context":
		if hasattr(hooks, hook):
			delattr(hooks, hook)

	setattr(hooks, key, value)
	dontmanage.client_cache.delete_value("app_hooks")
