# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.core.page.permission_manager.permission_manager import add, reset, update
from dontmanage.custom.doctype.property_setter.property_setter import make_property_setter
from dontmanage.desk.form.load import get_docinfo, getdoc, getdoctype
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils.file_manager import save_file

test_dependencies = ["Blog Category", "Blogger"]


class TestFormLoad(DontManageTestCase):
	def test_load(self):
		getdoctype("DocType")
		meta = list(filter(lambda d: d.name == "DocType", dontmanage.response.docs))[0]
		self.assertEqual(meta.name, "DocType")
		self.assertTrue(meta.get("__js"))

		dontmanage.response.docs = []
		getdoctype("Event")
		meta = list(filter(lambda d: d.name == "Event", dontmanage.response.docs))[0]
		self.assertTrue(meta.get("__calendar_js"))

	def test_fieldlevel_permissions_in_load(self):
		blog = dontmanage.get_doc(
			{
				"doctype": "Blog Post",
				"blog_category": "-test-blog-category-1",
				"blog_intro": "Test Blog Intro",
				"blogger": "_Test Blogger 1",
				"content": "Test Blog Content",
				"title": f"_Test Blog Post {dontmanage.utils.now()}",
				"published": 0,
			}
		)

		blog.insert()

		user = dontmanage.get_doc("User", "test@example.com")

		user_roles = dontmanage.get_roles()
		user.remove_roles(*user_roles)
		user.add_roles("Blogger")

		blog_post_property_setter = make_property_setter("Blog Post", "published", "permlevel", 1, "Int")
		reset("Blog Post")

		# test field level permission before role level permissions are defined
		dontmanage.set_user(user.name)
		blog_doc = get_blog(blog.name)

		with self.assertRaises(AttributeError):
			blog_doc.published

		# this will be ignored because user does not
		# have write access on `published` field (or on permlevel 1 fields)
		blog_doc.published = 1
		blog_doc.save()

		# since published field has higher permlevel
		self.assertEqual(blog_doc.published, 0)

		# test field level permission after role level permissions are defined
		dontmanage.set_user("Administrator")
		add("Blog Post", "Website Manager", 1)
		update("Blog Post", "Website Manager", 1, "write", 1)

		dontmanage.set_user(user.name)
		blog_doc = get_blog(blog.name)

		self.assertEqual(blog_doc.name, blog.name)
		# since published field has higher permlevel
		with self.assertRaises(AttributeError):
			blog_doc.published

		# this will be ignored because user does not
		# have write access on `published` field (or on permlevel 1 fields)
		blog_doc.published = 1
		blog_doc.save()

		# since published field has higher permlevel
		self.assertEqual(blog_doc.published, 0)

		dontmanage.set_user("Administrator")
		user.add_roles("Website Manager")
		dontmanage.set_user(user.name)

		doc = dontmanage.get_doc("Blog Post", blog.name)
		doc.published = 1
		doc.save()

		blog_doc = get_blog(blog.name)
		# now user should be allowed to read field with higher permlevel
		# (after adding Website Manager role)
		self.assertEqual(blog_doc.published, 1)

		dontmanage.set_user("Administrator")

		# reset user roles
		user.remove_roles("Blogger", "Website Manager")
		user.add_roles(*user_roles)

		blog_doc.delete()
		dontmanage.delete_doc(blog_post_property_setter.doctype, blog_post_property_setter.name)

	def test_fieldlevel_permissions_in_load_for_child_table(self):
		contact = dontmanage.new_doc("Contact")
		contact.first_name = "_Test Contact 1"
		contact.append("phone_nos", {"phone": "123456"})
		contact.insert()

		user = dontmanage.get_doc("User", "test@example.com")

		user_roles = dontmanage.get_roles()
		user.remove_roles(*user_roles)
		user.add_roles("Accounts User")

		make_property_setter("Contact Phone", "phone", "permlevel", 1, "Int")
		reset("Contact Phone")
		add("Contact", "Sales User", 1)
		update("Contact", "Sales User", 1, "write", 1)

		dontmanage.set_user(user.name)

		contact = dontmanage.get_doc("Contact", "_Test Contact 1")

		contact.phone_nos[0].phone = "654321"
		contact.save()

		self.assertEqual(contact.phone_nos[0].phone, "123456")

		dontmanage.set_user("Administrator")
		user.add_roles("Sales User")
		dontmanage.set_user(user.name)

		contact.phone_nos[0].phone = "654321"
		contact.save()

		contact = dontmanage.get_doc("Contact", "_Test Contact 1")
		self.assertEqual(contact.phone_nos[0].phone, "654321")

		dontmanage.set_user("Administrator")

		# reset user roles
		user.remove_roles("Accounts User", "Sales User")
		user.add_roles(*user_roles)

		contact.delete()

	def test_get_doc_info(self):
		note = dontmanage.new_doc("Note")
		note.content = "some content"
		note.title = dontmanage.generate_hash(length=20)
		note.insert()

		note.content = "new content"
		# trigger a version
		note.save(ignore_version=False)

		note.add_comment(text="test")

		note.add_tag("test_tag")
		note.add_tag("more_tag")

		# empty attachment
		save_file("test_file", b"", note.doctype, note.name, decode=True)

		dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"content": "test email",
				"reference_doctype": note.doctype,
				"reference_name": note.name,
			}
		).insert()

		get_docinfo(note)
		docinfo = dontmanage.response["docinfo"]

		self.assertEqual(len(docinfo.comments), 1)
		self.assertIn("test", docinfo.comments[0].content)

		self.assertGreaterEqual(len(docinfo.versions), 1)

		self.assertEqual(set(docinfo.tags.split(",")), {"more_tag", "test_tag"})

		self.assertEqual(len(docinfo.attachments), 1)
		self.assertIn("test_file", docinfo.attachments[0].file_name)

		self.assertEqual(len(docinfo.communications), 1)
		self.assertIn("email", docinfo.communications[0].content)
		note.delete()


def get_blog(blog_name):
	dontmanage.response.docs = []
	getdoc("Blog Post", blog_name)
	doc = dontmanage.response.docs[0]
	return doc
