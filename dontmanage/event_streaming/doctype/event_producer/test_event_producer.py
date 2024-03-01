# Copyright (c) 2019, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import json

import dontmanage
from dontmanage.core.doctype.user.user import generate_keys
from dontmanage.event_streaming.doctype.event_producer.event_producer import pull_from_node
from dontmanage.dontmanageclient import DontManageClient
from dontmanage.query_builder.utils import db_type_is
from dontmanage.tests.test_query_builder import run_only_if
from dontmanage.tests.utils import DontManageTestCase

producer_url = "http://test_site_producer:8000"


class TestEventProducer(DontManageTestCase):
	def setUp(self):
		create_event_producer(producer_url)

	def tearDown(self):
		unsubscribe_doctypes(producer_url)

	def test_insert(self):
		producer = get_remote_site()
		producer_doc = insert_into_producer(producer, "test creation 1 sync")
		self.pull_producer_data()
		self.assertTrue(dontmanage.db.exists("ToDo", producer_doc.name))

	def test_update(self):
		producer = get_remote_site()
		producer_doc = insert_into_producer(producer, "test update 1")
		producer_doc["description"] = "test update 2"
		producer_doc = producer.update(producer_doc)
		self.pull_producer_data()
		local_doc = dontmanage.get_doc(producer_doc.doctype, producer_doc.name)
		self.assertEqual(local_doc.description, producer_doc.description)

	def test_delete(self):
		producer = get_remote_site()
		producer_doc = insert_into_producer(producer, "test delete sync")
		self.pull_producer_data()
		self.assertTrue(dontmanage.db.exists("ToDo", producer_doc.name))
		producer.delete("ToDo", producer_doc.name)
		self.pull_producer_data()
		self.assertFalse(dontmanage.db.exists("ToDo", producer_doc.name))

	def test_child_table_sync_with_dependencies(self):
		producer = get_remote_site()
		producer_user = dontmanage._dict(
			doctype="User",
			email="test_user@sync.com",
			send_welcome_email=0,
			first_name="Test Sync User",
			enabled=1,
			roles=[{"role": "System Manager"}],
		)
		delete_on_remote_if_exists(producer, "User", {"email": producer_user.email})
		dontmanage.db.delete("User", {"email": producer_user.email})
		producer_user = producer.insert(producer_user)

		producer_note = dontmanage._dict(
			doctype="Note", title="test child table dependency sync", seen_by=[{"user": producer_user.name}]
		)
		delete_on_remote_if_exists(producer, "Note", {"title": producer_note.title})
		dontmanage.db.delete("Note", {"title": producer_note.title})
		producer_note = producer.insert(producer_note)

		self.pull_producer_data()
		self.assertTrue(dontmanage.db.exists("User", producer_user.name))
		if self.assertTrue(dontmanage.db.exists("Note", producer_note.name)):
			local_note = dontmanage.get_doc("Note", producer_note.name)
			self.assertEqual(len(local_note.seen_by), 1)

	def test_dynamic_link_dependencies_synced(self):
		producer = get_remote_site()
		# unsubscribe for Note to check whether dependency is fulfilled
		event_producer = dontmanage.get_doc("Event Producer", producer_url, for_update=True)
		event_producer.producer_doctypes = []
		event_producer.append("producer_doctypes", {"ref_doctype": "ToDo", "use_same_name": 1})
		event_producer.save()

		producer_link_doc = dontmanage._dict(doctype="Note", title="Test Dynamic Link 1")

		delete_on_remote_if_exists(producer, "Note", {"title": producer_link_doc.title})
		dontmanage.db.delete("Note", {"title": producer_link_doc.title})
		producer_link_doc = producer.insert(producer_link_doc)
		producer_doc = dontmanage._dict(
			doctype="ToDo",
			description="Test Dynamic Link 2",
			assigned_by="Administrator",
			reference_type="Note",
			reference_name=producer_link_doc.name,
		)
		producer_doc = producer.insert(producer_doc)

		self.pull_producer_data()

		# check dynamic link dependency created
		self.assertTrue(dontmanage.db.exists("Note", producer_link_doc.name))
		self.assertEqual(
			producer_link_doc.name, dontmanage.db.get_value("ToDo", producer_doc.name, "reference_name")
		)

		reset_configuration(producer_url)

	def test_naming_configuration(self):
		# test with use_same_name = 0
		producer = get_remote_site()
		event_producer = dontmanage.get_doc("Event Producer", producer_url, for_update=True)
		event_producer.producer_doctypes = []
		event_producer.append("producer_doctypes", {"ref_doctype": "ToDo", "use_same_name": 0})
		event_producer.save()

		producer_doc = insert_into_producer(producer, "test different name sync")
		self.pull_producer_data()
		self.assertTrue(
			dontmanage.db.exists(
				"ToDo", {"remote_docname": producer_doc.name, "remote_site_name": producer_url}
			)
		)

		reset_configuration(producer_url)

	def test_conditional_events(self):
		producer = get_remote_site()

		# Add Condition
		event_producer = dontmanage.get_doc("Event Producer", producer_url)
		note_producer_entry = [x for x in event_producer.producer_doctypes if x.ref_doctype == "Note"][0]
		note_producer_entry.condition = "doc.public == 1"
		event_producer.save()

		# Make test doc
		producer_note1 = dontmanage._dict(doctype="Note", public=0, title="test conditional sync")
		delete_on_remote_if_exists(producer, "Note", {"title": producer_note1["title"]})
		producer_note1 = producer.insert(producer_note1)

		# Make Update
		producer_note1["content"] = "Test Conditional Sync Content"
		producer_note1 = producer.update(producer_note1)

		self.pull_producer_data()

		# Check if synced here
		self.assertFalse(dontmanage.db.exists("Note", producer_note1.name))

		# Lets satisfy the condition
		producer_note1["public"] = 1
		producer_note1 = producer.update(producer_note1)

		self.pull_producer_data()

		# it should sync now
		self.assertTrue(dontmanage.db.exists("Note", producer_note1.name))
		local_note = dontmanage.get_doc("Note", producer_note1.name)
		self.assertEqual(local_note.content, producer_note1.content)

		reset_configuration(producer_url)

	def test_conditional_events_with_cmd(self):
		producer = get_remote_site()

		# Add Condition
		event_producer = dontmanage.get_doc("Event Producer", producer_url)
		note_producer_entry = [x for x in event_producer.producer_doctypes if x.ref_doctype == "Note"][0]
		note_producer_entry.condition = (
			"cmd: dontmanage.event_streaming.doctype.event_producer.test_event_producer.can_sync_note"
		)
		event_producer.save()

		# Make test doc
		producer_note1 = dontmanage._dict(doctype="Note", public=0, title="test conditional sync cmd")
		delete_on_remote_if_exists(producer, "Note", {"title": producer_note1["title"]})
		producer_note1 = producer.insert(producer_note1)

		# Make Update
		producer_note1["content"] = "Test Conditional Sync Content"
		producer_note1 = producer.update(producer_note1)

		self.pull_producer_data()

		# Check if synced here
		self.assertFalse(dontmanage.db.exists("Note", producer_note1.name))

		# Lets satisfy the condition
		producer_note1["public"] = 1
		producer_note1 = producer.update(producer_note1)

		self.pull_producer_data()

		# it should sync now
		self.assertTrue(dontmanage.db.exists("Note", producer_note1.name))
		local_note = dontmanage.get_doc("Note", producer_note1.name)
		self.assertEqual(local_note.content, producer_note1.content)

		reset_configuration(producer_url)

	def test_update_log(self):
		producer = get_remote_site()
		producer_doc = insert_into_producer(producer, "test update log")
		update_log_doc = producer.get_value(
			"Event Update Log", "docname", {"docname": producer_doc.get("name")}
		)
		self.assertEqual(update_log_doc.get("docname"), producer_doc.get("name"))

	def test_event_sync_log(self):
		producer = get_remote_site()
		producer_doc = insert_into_producer(producer, "test event sync log")
		self.pull_producer_data()
		self.assertTrue(dontmanage.db.exists("Event Sync Log", {"docname": producer_doc.name}))

	def pull_producer_data(self):
		pull_from_node(producer_url)

	def test_mapping(self):
		producer = get_remote_site()
		event_producer = dontmanage.get_doc("Event Producer", producer_url, for_update=True)
		event_producer.producer_doctypes = []
		mapping = [{"local_fieldname": "description", "remote_fieldname": "content"}]
		event_producer.append(
			"producer_doctypes",
			{
				"ref_doctype": "ToDo",
				"use_same_name": 1,
				"has_mapping": 1,
				"mapping": get_mapping("ToDo to Note", "ToDo", "Note", mapping),
			},
		)
		event_producer.save()

		producer_note = dontmanage._dict(doctype="Note", title="Test Mapping", content="Test Mapping")
		delete_on_remote_if_exists(producer, "Note", {"title": producer_note.title})
		producer_note = producer.insert(producer_note)
		self.pull_producer_data()
		# check inserted
		self.assertTrue(dontmanage.db.exists("ToDo", {"description": producer_note.content}))

		# update in producer
		producer_note["content"] = "test mapped doc update sync"
		producer_note = producer.update(producer_note)
		self.pull_producer_data()

		# check updated
		self.assertTrue(dontmanage.db.exists("ToDo", {"description": producer_note["content"]}))

		producer.delete("Note", producer_note.name)
		self.pull_producer_data()
		# check delete
		self.assertFalse(dontmanage.db.exists("ToDo", {"description": producer_note.content}))

		reset_configuration(producer_url)

	def test_inner_mapping(self):
		producer = get_remote_site()

		setup_event_producer_for_inner_mapping()
		producer_note = dontmanage._dict(
			doctype="Note", title="Inner Mapping Tester", content="Test Inner Mapping"
		)
		delete_on_remote_if_exists(producer, "Note", {"title": producer_note.title})
		producer_note = producer.insert(producer_note)
		self.pull_producer_data()

		# check dependency inserted
		self.assertTrue(dontmanage.db.exists("Role", {"role_name": producer_note.title}))
		# check doc inserted
		self.assertTrue(dontmanage.db.exists("ToDo", {"description": producer_note.content}))

		reset_configuration(producer_url)


def can_sync_note(consumer, doc, update_log):
	return doc.public == 1


def setup_event_producer_for_inner_mapping():
	event_producer = dontmanage.get_doc("Event Producer", producer_url, for_update=True)
	event_producer.producer_doctypes = []
	inner_mapping = [{"local_fieldname": "role_name", "remote_fieldname": "title"}]
	inner_map = get_mapping("Role to Note Dependency Creation", "Role", "Note", inner_mapping)
	mapping = [
		{
			"local_fieldname": "description",
			"remote_fieldname": "content",
		},
		{
			"local_fieldname": "role",
			"remote_fieldname": "title",
			"mapping_type": "Document",
			"mapping": inner_map,
			"remote_value_filters": json.dumps({"title": "title"}),
		},
	]
	event_producer.append(
		"producer_doctypes",
		{
			"ref_doctype": "ToDo",
			"use_same_name": 1,
			"has_mapping": 1,
			"mapping": get_mapping("ToDo to Note Mapping", "ToDo", "Note", mapping),
		},
	)
	event_producer.save()
	return event_producer


def insert_into_producer(producer, description):
	# create and insert todo on remote site
	todo = dict(doctype="ToDo", description=description, assigned_by="Administrator")
	return producer.insert(todo)


def delete_on_remote_if_exists(producer, doctype, filters):
	remote_doc = producer.get_value(doctype, "name", filters)
	if remote_doc:
		producer.delete(doctype, remote_doc.get("name"))


def get_mapping(mapping_name, local, remote, field_map):
	name = dontmanage.db.exists("Document Type Mapping", mapping_name)
	if name:
		doc = dontmanage.get_doc("Document Type Mapping", name)
	else:
		doc = dontmanage.new_doc("Document Type Mapping")

	doc.mapping_name = mapping_name
	doc.local_doctype = local
	doc.remote_doctype = remote
	for entry in field_map:
		doc.append("field_mapping", entry)
	doc.save()
	return doc.name


def create_event_producer(producer_url):
	if dontmanage.db.exists("Event Producer", producer_url):
		event_producer = dontmanage.get_doc("Event Producer", producer_url)
		for entry in event_producer.producer_doctypes:
			entry.unsubscribe = 0
		event_producer.save()
		return

	generate_keys("Administrator")

	producer_site = connect()

	response = producer_site.post_api(
		"dontmanage.core.doctype.user.user.generate_keys", params={"user": "Administrator"}
	)

	api_secret = response.get("api_secret")

	response = producer_site.get_value("User", "api_key", {"name": "Administrator"})
	api_key = response.get("api_key")

	event_producer = dontmanage.new_doc("Event Producer")
	event_producer.producer_doctypes = []
	event_producer.producer_url = producer_url
	event_producer.append("producer_doctypes", {"ref_doctype": "ToDo", "use_same_name": 1})
	event_producer.append("producer_doctypes", {"ref_doctype": "Note", "use_same_name": 1})
	event_producer.user = "Administrator"
	event_producer.api_key = api_key
	event_producer.api_secret = api_secret
	event_producer.save()


def reset_configuration(producer_url):
	event_producer = dontmanage.get_doc("Event Producer", producer_url, for_update=True)
	event_producer.producer_doctypes = []
	event_producer.conditions = []
	event_producer.producer_url = producer_url
	event_producer.append("producer_doctypes", {"ref_doctype": "ToDo", "use_same_name": 1})
	event_producer.append("producer_doctypes", {"ref_doctype": "Note", "use_same_name": 1})
	event_producer.user = "Administrator"
	event_producer.save()


def get_remote_site():
	producer_doc = dontmanage.get_doc("Event Producer", producer_url)
	producer_site = DontManageClient(
		url=producer_doc.producer_url, username="Administrator", password="admin", verify=False
	)
	return producer_site


def unsubscribe_doctypes(producer_url):
	event_producer = dontmanage.get_doc("Event Producer", producer_url)
	for entry in event_producer.producer_doctypes:
		entry.unsubscribe = 1
	event_producer.save()


def connect():
	def _connect():
		return DontManageClient(url=producer_url, username="Administrator", password="admin", verify=False)

	try:
		return _connect()
	except Exception:
		return _connect()