# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import re

import dontmanage
from dontmanage.model.document import Document

NAME_PATTERN = re.compile("[%'\"#*?`]")


class Note(Document):
	def autoname(self):
		# replace forbidden characters
		self.name = NAME_PATTERN.sub("", self.title.strip())

	def validate(self):
		if self.notify_on_login and not self.expire_notification_on:

			# expire this notification in a week (default)
			self.expire_notification_on = dontmanage.utils.add_days(self.creation, 7)

	def before_print(self, settings=None):
		self.print_heading = self.name
		self.sub_heading = ""


@dontmanage.whitelist()
def mark_as_seen(note):
	note = dontmanage.get_doc("Note", note)
	if dontmanage.session.user not in [d.user for d in note.seen_by]:
		note.append("seen_by", {"user": dontmanage.session.user})
		note.save(ignore_version=True, ignore_permissions=True)


def get_permission_query_conditions(user):
	if not user:
		user = dontmanage.session.user

	if user == "Administrator":
		return ""

	return f"""(`tabNote`.public=1 or `tabNote`.owner={dontmanage.db.escape(user)})"""


def has_permission(doc, ptype, user):
	if doc.public == 1 or user == "Administrator":
		return True

	if user == doc.owner:
		return True

	return False
