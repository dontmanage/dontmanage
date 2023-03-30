# Copyright (c) 2021, DontManage Technologies and contributors
# For license information, please see license.txt

import dontmanage
from dontmanage.model.document import Document
from dontmanage.realtime import get_website_room


class DiscussionReply(Document):
	def on_update(self):
		dontmanage.publish_realtime(
			event="update_message",
			room=get_website_room(),
			message={"reply": dontmanage.utils.md_to_html(self.reply), "reply_name": self.name},
			after_commit=True,
		)

	def after_insert(self):
		replies = dontmanage.db.count("Discussion Reply", {"topic": self.topic})
		topic_info = dontmanage.get_all(
			"Discussion Topic",
			{"name": self.topic},
			["reference_doctype", "reference_docname", "name", "title", "owner", "creation"],
		)

		template = dontmanage.render_template(
			"dontmanage/templates/discussions/reply_card.html",
			{
				"reply": self,
				"topic": {"name": self.topic},
				"loop": {"index": replies},
				"single_thread": True if not topic_info[0].title else False,
			},
		)

		sidebar = dontmanage.render_template(
			"dontmanage/templates/discussions/sidebar.html", {"topic": topic_info[0]}
		)

		new_topic_template = dontmanage.render_template(
			"dontmanage/templates/discussions/reply_section.html", {"topic": topic_info[0]}
		)

		dontmanage.publish_realtime(
			event="publish_message",
			room=get_website_room(),
			message={
				"template": template,
				"topic_info": topic_info[0],
				"sidebar": sidebar,
				"new_topic_template": new_topic_template,
				"reply_owner": self.owner,
			},
			after_commit=True,
		)

	def after_delete(self):
		dontmanage.publish_realtime(
			event="delete_message",
			room=get_website_room(),
			message={"reply_name": self.name},
			after_commit=True,
		)


@dontmanage.whitelist()
def delete_message(reply_name):
	owner = dontmanage.db.get_value("Discussion Reply", reply_name, "owner")
	if owner == dontmanage.session.user:
		dontmanage.delete_doc("Discussion Reply", reply_name)
