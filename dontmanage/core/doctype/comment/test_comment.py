# Copyright (c) 2019, DontManage Technologies and Contributors
# License: MIT. See LICENSE
import json

import dontmanage
from dontmanage.tests.utils import DontManageTestCase


class TestComment(DontManageTestCase):
	def tearDown(self):
		dontmanage.form_dict.comment = None
		dontmanage.form_dict.comment_email = None
		dontmanage.form_dict.comment_by = None
		dontmanage.form_dict.reference_doctype = None
		dontmanage.form_dict.reference_name = None
		dontmanage.form_dict.route = None
		dontmanage.local.request_ip = None

	def test_comment_creation(self):
		test_doc = dontmanage.get_doc(dict(doctype="ToDo", description="test"))
		test_doc.insert()
		comment = test_doc.add_comment("Comment", "test comment")

		test_doc.reload()

		# check if updated in _comments cache
		comments = json.loads(test_doc.get("_comments"))
		self.assertEqual(comments[0].get("name"), comment.name)
		self.assertEqual(comments[0].get("comment"), comment.content)

		# check document creation
		comment_1 = dontmanage.get_all(
			"Comment",
			fields=["*"],
			filters=dict(reference_doctype=test_doc.doctype, reference_name=test_doc.name),
		)[0]

		self.assertEqual(comment_1.content, "test comment")

	# test via blog
	def test_public_comment(self):
		from dontmanage.website.doctype.blog_post.test_blog_post import make_test_blog

		test_blog = make_test_blog()

		dontmanage.db.delete("Comment", {"reference_doctype": "Blog Post"})

		from dontmanage.templates.includes.comments.comments import add_comment

		dontmanage.form_dict.comment = "Good comment with 10 chars"
		dontmanage.form_dict.comment_email = "test@test.com"
		dontmanage.form_dict.comment_by = "Good Tester"
		dontmanage.form_dict.reference_doctype = "Blog Post"
		dontmanage.form_dict.reference_name = test_blog.name
		dontmanage.form_dict.route = test_blog.route
		dontmanage.local.request_ip = "127.0.0.1"

		add_comment()

		self.assertEqual(
			dontmanage.get_all(
				"Comment",
				fields=["*"],
				filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
			)[0].published,
			1,
		)

		dontmanage.db.delete("Comment", {"reference_doctype": "Blog Post"})

		dontmanage.form_dict.comment = "pleez vizits my site http://mysite.com"
		dontmanage.form_dict.comment_by = "bad commentor"

		add_comment()

		self.assertEqual(
			len(
				dontmanage.get_all(
					"Comment",
					fields=["*"],
					filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
				)
			),
			0,
		)

		# test for filtering html and css injection elements
		dontmanage.db.delete("Comment", {"reference_doctype": "Blog Post"})

		dontmanage.form_dict.comment = "<script>alert(1)</script>Comment"
		dontmanage.form_dict.comment_by = "hacker"

		add_comment()

		self.assertEqual(
			dontmanage.get_all(
				"Comment",
				fields=["content"],
				filters=dict(reference_doctype=test_blog.doctype, reference_name=test_blog.name),
			)[0]["content"],
			"Comment",
		)

		test_blog.delete()
