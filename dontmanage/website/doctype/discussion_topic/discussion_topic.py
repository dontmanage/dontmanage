# Copyright (c) 2021, FOSS United and contributors
# For license information, please see license.txt

import dontmanage
from dontmanage.model.document import Document


class DiscussionTopic(Document):
	pass


@dontmanage.whitelist()
def submit_discussion(doctype, docname, reply, title, topic_name=None, reply_name=None):

	if reply_name:
		doc = dontmanage.get_doc("Discussion Reply", reply_name)
		doc.reply = reply
		doc.save(ignore_permissions=True)
		return

	if topic_name:
		save_message(reply, topic_name)
		return topic_name

	topic = dontmanage.get_doc(
		{
			"doctype": "Discussion Topic",
			"title": title,
			"reference_doctype": doctype,
			"reference_docname": docname,
		}
	)
	topic.save(ignore_permissions=True)
	save_message(reply, topic.name)
	return topic.name


def save_message(reply, topic):
	dontmanage.get_doc({"doctype": "Discussion Reply", "reply": reply, "topic": topic}).save(
		ignore_permissions=True
	)


@dontmanage.whitelist(allow_guest=True)
def get_docname(route):
	if not route:
		route = dontmanage.db.get_single_value("Website Settings", "home_page")
	return dontmanage.db.get_value("Web Page", {"route": route}, ["name"])
