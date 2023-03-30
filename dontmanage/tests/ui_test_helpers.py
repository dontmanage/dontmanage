import dontmanage
from dontmanage import _
from dontmanage.utils import add_to_date, now

UI_TEST_USER = "dontmanage@example.com"


def whitelist_for_tests(fn):
	if dontmanage.request and not (dontmanage.flags.in_test or getattr(dontmanage.local, "dev_server", 0)):
		dontmanage.throw("Cannot run UI tests. Use a development server with `bench start`")

	return dontmanage.whitelist()(fn)


@whitelist_for_tests
def create_if_not_exists(doc):
	"""Create records if they dont exist.
	Will check for uniqueness by checking if a record exists with these field value pairs

	:param doc: dict of field value pairs. can be a list of dict for multiple records.
	"""

	doc = dontmanage.parse_json(doc)

	if not isinstance(doc, list):
		docs = [doc]
	else:
		docs = doc

	names = []
	for doc in docs:
		doc = dontmanage._dict(doc)
		filters = doc.copy()
		filters.pop("doctype")
		name = dontmanage.db.exists(doc.doctype, filters)
		if not name:
			d = dontmanage.get_doc(doc)
			d.insert(ignore_permissions=True)
			name = d.name
		names.append(name)

	return names


@whitelist_for_tests
def create_todo_records():
	dontmanage.db.truncate("ToDo")

	dontmanage.get_doc(
		{
			"doctype": "ToDo",
			"date": add_to_date(now(), days=7),
			"description": "this is first todo",
		}
	).insert()
	dontmanage.get_doc(
		{
			"doctype": "ToDo",
			"date": add_to_date(now(), days=-7),
			"description": "this is second todo",
		}
	).insert()
	dontmanage.get_doc(
		{
			"doctype": "ToDo",
			"date": add_to_date(now(), months=2),
			"description": "this is third todo",
		}
	).insert()
	dontmanage.get_doc(
		{
			"doctype": "ToDo",
			"date": add_to_date(now(), months=-2),
			"description": "this is fourth todo",
		}
	).insert()


@whitelist_for_tests
def clear_notes():
	for note in dontmanage.get_all("Note", pluck="name"):
		dontmanage.delete_doc("Note", note, force=True)


@whitelist_for_tests
def create_communication_record():
	doc = dontmanage.get_doc(
		{
			"doctype": "Communication",
			"recipients": "test@gmail.com",
			"subject": "Test Form Communication 1",
			"communication_date": dontmanage.utils.now_datetime(),
		}
	)
	doc.insert()
	return doc


@whitelist_for_tests
def setup_workflow():
	from dontmanage.workflow.doctype.workflow.test_workflow import create_todo_workflow

	create_todo_workflow()
	create_todo_records()
	dontmanage.clear_cache()


@whitelist_for_tests
def create_contact_phone_nos_records():
	if dontmanage.get_all("Contact", {"first_name": "Test Contact"}):
		return

	doc = dontmanage.new_doc("Contact")
	doc.first_name = "Test Contact"
	for index in range(1000):
		doc.append("phone_nos", {"phone": f"123456{index}"})
	doc.insert()


@whitelist_for_tests
def create_doctype(name, fields):
	fields = dontmanage.parse_json(fields)
	if dontmanage.db.exists("DocType", name):
		return
	dontmanage.get_doc(
		{
			"doctype": "DocType",
			"module": "Core",
			"custom": 1,
			"fields": fields,
			"permissions": [{"role": "System Manager", "read": 1}],
			"name": name,
		}
	).insert()


@whitelist_for_tests
def create_child_doctype(name, fields):
	fields = dontmanage.parse_json(fields)
	if dontmanage.db.exists("DocType", name):
		return
	dontmanage.get_doc(
		{
			"doctype": "DocType",
			"module": "Core",
			"istable": 1,
			"custom": 1,
			"fields": fields,
			"permissions": [{"role": "System Manager", "read": 1}],
			"name": name,
		}
	).insert()


@whitelist_for_tests
def create_contact_records():
	if dontmanage.get_all("Contact", {"first_name": "Test Form Contact 1"}):
		return

	insert_contact("Test Form Contact 1", "12345")
	insert_contact("Test Form Contact 2", "54321")
	insert_contact("Test Form Contact 3", "12345")


@whitelist_for_tests
def create_multiple_todo_records():
	if dontmanage.get_all("ToDo", {"description": "Multiple ToDo 1"}):
		return

	values = [(f"100{i}", f"Multiple ToDo {i}") for i in range(1, 1002)]

	dontmanage.db.bulk_insert("ToDo", fields=["name", "description"], values=set(values))


def insert_contact(first_name, phone_number):
	doc = dontmanage.get_doc({"doctype": "Contact", "first_name": first_name})
	doc.append("phone_nos", {"phone": phone_number})
	doc.insert()


@whitelist_for_tests
def create_form_tour():
	if dontmanage.db.exists("Form Tour", {"name": "Test Form Tour"}):
		return

	tour = dontmanage.get_doc(
		{
			"doctype": "Form Tour",
			"title": "Test Form Tour",
			"reference_doctype": "Contact",
			"save_on_complete": 1,
			"steps": [
				{
					"title": "Test Title 1",
					"description": "Test Description 1",
					"has_next_condition": 1,
					"next_step_condition": "eval: doc.first_name",
					"fieldname": "first_name",
					"fieldtype": "Data",
				},
				{
					"title": "Test Title 2",
					"description": "Test Description 2",
					"has_next_condition": 1,
					"next_step_condition": "eval: doc.last_name",
					"fieldname": "last_name",
					"fieldtype": "Data",
				},
				{
					"title": "Test Title 3",
					"description": "Test Description 3",
					"fieldname": "phone_nos",
					"fieldtype": "Table",
				},
				{
					"title": "Test Title 4",
					"description": "Test Description 4",
					"is_table_field": 1,
					"parent_fieldname": "phone_nos",
					"next_step_condition": "eval: doc.phone",
					"has_next_condition": 1,
					"fieldname": "phone",
					"fieldtype": "Data",
				},
			],
		}
	)
	tour.insert()


@whitelist_for_tests
def create_data_for_discussions():
	web_page = create_web_page("Test page for discussions", "test-page-discussions", False)
	create_topic_and_reply(web_page)
	create_web_page("Test single thread discussion", "test-single-thread", True)


def create_web_page(title, route, single_thread):
	web_page = dontmanage.db.exists("Web Page", {"route": route})
	if web_page:
		return web_page
	web_page = dontmanage.get_doc(
		{"doctype": "Web Page", "title": title, "route": route, "published": True}
	)
	web_page.save()

	web_page.append(
		"page_blocks",
		{
			"web_template": "Discussions",
			"web_template_values": dontmanage.as_json(
				{
					"title": "Discussions",
					"cta_title": "New Discussion",
					"docname": web_page.name,
					"single_thread": single_thread,
				}
			),
		},
	)
	web_page.save()

	return web_page.name


def create_topic_and_reply(web_page):
	topic = dontmanage.db.exists(
		"Discussion Topic", {"reference_doctype": "Web Page", "reference_docname": web_page}
	)

	if not topic:
		topic = dontmanage.get_doc(
			{
				"doctype": "Discussion Topic",
				"reference_doctype": "Web Page",
				"reference_docname": web_page,
				"title": "Test Topic",
			}
		)
		topic.save()

		reply = dontmanage.get_doc(
			{"doctype": "Discussion Reply", "topic": topic.name, "reply": "This is a test reply"}
		)

		reply.save()


@whitelist_for_tests
def update_webform_to_multistep():
	if not dontmanage.db.exists("Web Form", "update-profile-duplicate"):
		doc = dontmanage.get_doc("Web Form", "edit-profile")
		_doc = dontmanage.copy_doc(doc)
		_doc.title = "update-profile-duplicate"
		_doc.route = "update-profile-duplicate"
		_doc.web_form_fields[5].fieldtype = "Page Break"
		_doc.is_standard = False
		_doc.save()


@whitelist_for_tests
def update_child_table(name):
	doc = dontmanage.get_doc("DocType", name)
	if len(doc.fields) == 1:
		doc.append(
			"fields",
			{
				"fieldname": "doctype_to_link",
				"fieldtype": "Link",
				"in_list_view": 1,
				"label": "Doctype to Link",
				"options": "Doctype to Link",
			},
		)

		doc.save()


@whitelist_for_tests
def insert_doctype_with_child_table_record(name):
	if dontmanage.get_all(name, {"title": "Test Grid Search"}):
		return

	def insert_child(doc, data, barcode, check, rating, duration, date):
		doc.append(
			"child_table_1",
			{
				"data": data,
				"barcode": barcode,
				"check": check,
				"rating": rating,
				"duration": duration,
				"date": date,
			},
		)

	doc = dontmanage.new_doc(name)
	doc.title = "Test Grid Search"
	doc.append("child_table", {"title": "Test Grid Search"})

	insert_child(doc, "Data", "09709KJKKH2432", 1, 0.5, 266851, "2022-02-21")
	insert_child(doc, "Test", "09209KJHKH2432", 1, 0.8, 547877, "2021-05-27")
	insert_child(doc, "New", "09709KJHYH1132", 0, 0.1, 3, "2019-03-02")
	insert_child(doc, "Old", "09701KJHKH8750", 0, 0, 127455, "2022-01-11")
	insert_child(doc, "Alpha", "09204KJHKH2432", 0, 0.6, 364, "2019-12-31")
	insert_child(doc, "Delta", "09709KSPIO2432", 1, 0.9, 1242000, "2020-04-21")
	insert_child(doc, "Update", "76989KJLVA2432", 0, 1, 183845, "2022-02-10")
	insert_child(doc, "Delete", "29189KLHVA1432", 0, 0, 365647, "2021-05-07")
	insert_child(doc, "Make", "09689KJHAA2431", 0, 0.3, 24, "2020-11-11")
	insert_child(doc, "Create", "09709KLKKH2432", 1, 0.3, 264851, "2021-02-21")
	insert_child(doc, "Group", "09209KJLKH2432", 1, 0.8, 537877, "2020-03-15")
	insert_child(doc, "Slide", "01909KJHYH1132", 0, 0.5, 9, "2018-03-02")
	insert_child(doc, "Drop", "09701KJHKH8750", 1, 0, 127255, "2018-01-01")
	insert_child(doc, "Beta", "09204QJHKN2432", 0, 0.6, 354, "2017-12-30")
	insert_child(doc, "Flag", "09709KXPIP2432", 1, 0, 1241000, "2021-04-21")
	insert_child(doc, "Upgrade", "75989ZJLVA2432", 0.8, 1, 183645, "2020-08-13")
	insert_child(doc, "Down", "28189KLHRA1432", 1, 0, 362647, "2020-06-17")
	insert_child(doc, "Note", "09689DJHAA2431", 0, 0.1, 29, "2021-09-11")
	insert_child(doc, "Click", "08189DJHAA2431", 1, 0.3, 209, "2020-07-04")
	insert_child(doc, "Drag", "08189DIHAA2981", 0, 0.7, 342628, "2022-05-04")

	doc.insert()


@whitelist_for_tests
def insert_translations():
	translation = [
		{
			"doctype": "Translation",
			"language": "de",
			"source_text": "Other",
			"translated_text": "Sonstiges",
		},
		{
			"doctype": "Translation",
			"language": "de",
			"source_text": "Genderqueer",
			"translated_text": "Nichtbinär",
		},
		{
			"doctype": "Translation",
			"language": "de",
			"source_text": "Non-Conforming",
			"translated_text": "Nicht konform",
		},
		{
			"doctype": "Translation",
			"language": "de",
			"source_text": "Prefer not to say",
			"translated_text": "Keine Angabe",
		},
	]

	for doc in translation:
		if not dontmanage.db.exists("doc"):
			dontmanage.get_doc(doc).insert()


@whitelist_for_tests
def create_blog_post():

	blog_category = dontmanage.get_doc(
		{"name": "general", "doctype": "Blog Category", "title": "general"}
	).insert(ignore_if_duplicate=True)

	blogger = dontmanage.get_doc(
		{
			"name": "attachment blogger",
			"doctype": "Blogger",
			"full_name": "attachment blogger",
			"short_name": "attachment blogger",
		}
	).insert(ignore_if_duplicate=True)

	doc = dontmanage.get_doc(
		{
			"name": "test-blog-attachment-post",
			"doctype": "Blog Post",
			"title": "test-blog-attachment-post",
			"blog_category": blog_category.name,
			"blogger": blogger.name,
			"content_type": "Rich Text",
		},
	).insert(ignore_if_duplicate=True)

	return doc


def create_test_user():
	if dontmanage.db.exists("User", UI_TEST_USER):
		return

	user = dontmanage.new_doc("User")
	user.email = UI_TEST_USER
	user.first_name = "DontManage"
	user.new_password = dontmanage.local.conf.admin_password
	user.send_welcome_email = 0
	user.time_zone = "Asia/Kolkata"
	user.flags.ignore_password_policy = True
	user.insert(ignore_if_duplicate=True)

	user.reload()

	blocked_roles = {"Administrator", "Guest", "All"}
	all_roles = set(dontmanage.get_all("Role", pluck="name"))

	for role in all_roles - blocked_roles:
		user.append("roles", {"role": role})

	user.save()


@whitelist_for_tests
def setup_tree_doctype():
	dontmanage.delete_doc_if_exists("DocType", "Custom Tree")

	dontmanage.get_doc(
		{
			"doctype": "DocType",
			"module": "Core",
			"custom": 1,
			"fields": [
				{"fieldname": "tree", "fieldtype": "Data", "label": "Tree"},
			],
			"permissions": [{"role": "System Manager", "read": 1}],
			"name": "Custom Tree",
			"is_tree": True,
			"naming_rule": "By fieldname",
			"autoname": "field:tree",
		}
	).insert()

	if not dontmanage.db.exists("Custom Tree", "All Trees"):
		dontmanage.get_doc({"doctype": "Custom Tree", "tree": "All Trees"}).insert()


@whitelist_for_tests
def setup_image_doctype():
	dontmanage.delete_doc_if_exists("DocType", "Custom Image")

	dontmanage.get_doc(
		{
			"doctype": "DocType",
			"module": "Core",
			"custom": 1,
			"fields": [
				{"fieldname": "image", "fieldtype": "Attach Image", "label": "Image"},
			],
			"permissions": [{"role": "System Manager", "read": 1}],
			"name": "Custom Image",
			"image_field": "image",
		}
	).insert()


@whitelist_for_tests
def setup_inbox():
	dontmanage.db.delete("User Email")

	user = dontmanage.get_doc("User", dontmanage.session.user)
	user.append("user_emails", {"email_account": "Email Linking"})
	user.save()


@whitelist_for_tests
def setup_default_view(view, force_reroute=None):
	dontmanage.delete_doc_if_exists("Property Setter", "Event-main-default_view")
	dontmanage.delete_doc_if_exists("Property Setter", "Event-main-force_re_route_to_default_view")

	dontmanage.get_doc(
		{
			"is_system_generated": 0,
			"doctype_or_field": "DocType",
			"doc_type": "Event",
			"property": "default_view",
			"property_type": "Select",
			"value": view,
			"doctype": "Property Setter",
		}
	).insert()

	if force_reroute:
		dontmanage.get_doc(
			{
				"is_system_generated": 0,
				"doctype_or_field": "DocType",
				"doc_type": "Event",
				"property": "force_re_route_to_default_view",
				"property_type": "Check",
				"value": "1",
				"doctype": "Property Setter",
			}
		).insert()


@whitelist_for_tests
def create_note():
	if not dontmanage.db.exists("Note", "Routing Test"):
		dontmanage.get_doc({"doctype": "Note", "title": "Routing Test"}).insert()


@whitelist_for_tests
def create_kanban():
	if not dontmanage.db.exists("Custom Field", "Note-kanban"):
		dontmanage.get_doc(
			{
				"is_system_generated": 0,
				"dt": "Note",
				"label": "Kanban",
				"fieldname": "kanban",
				"insert_after": "seen_by",
				"fieldtype": "Select",
				"options": "Open\nClosed",
				"doctype": "Custom Field",
			}
		).insert()

	if not dontmanage.db.exists("Kanban Board", "_Note _Kanban"):
		dontmanage.get_doc(
			{
				"doctype": "Kanban Board",
				"name": "_Note _Kanban",
				"kanban_board_name": "_Note _Kanban",
				"reference_doctype": "Note",
				"field_name": "kanban",
				"private": 1,
				"show_labels": 0,
				"columns": [
					{
						"column_name": "Open",
						"status": "Active",
						"indicator": "Gray",
					},
					{
						"column_name": "Closed",
						"status": "Active",
						"indicator": "Gray",
					},
				],
			}
		).insert()


@whitelist_for_tests
def create_todo(description):
	dontmanage.get_doc({"doctype": "ToDo", "description": description}).insert()


@whitelist_for_tests
def create_admin_kanban():
	if not dontmanage.db.exists("Kanban Board", "Admin Kanban"):
		dontmanage.get_doc(
			{
				"doctype": "Kanban Board",
				"name": "Admin Kanban",
				"owner": "Administrator",
				"kanban_board_name": "Admin Kanban",
				"reference_doctype": "ToDo",
				"field_name": "status",
				"private": 0,
				"show_labels": 0,
				"columns": [
					{
						"column_name": "Open",
						"status": "Active",
						"indicator": "Gray",
					},
					{
						"column_name": "Closed",
						"status": "Active",
						"indicator": "Gray",
					},
				],
			}
		).insert()


@whitelist_for_tests
def add_remove_role(action, user, role):
	user_doc = dontmanage.get_doc("User", user)
	if action == "remove":
		user_doc.remove_roles(role)
	else:
		user_doc.add_roles(role)
