# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document

UNSEEN_NOTES_KEY = "unseen_notes::"


class Note(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.desk.doctype.note_seen_by.note_seen_by import NoteSeenBy
		from dontmanage.types import DF

		content: DF.TextEditor | None
		expire_notification_on: DF.Datetime | None
		notify_on_every_login: DF.Check
		notify_on_login: DF.Check
		public: DF.Check
		seen_by: DF.Table[NoteSeenBy]
		title: DF.Data
	# end: auto-generated types

	def validate(self):
		if self.notify_on_login and not self.expire_notification_on:
			# expire this notification in a week (default)
			self.expire_notification_on = dontmanage.utils.add_days(self.creation, 7)

		if not self.public and self.notify_on_login:
			self.notify_on_login = 0

		if not self.content:
			self.content = "<span></span>"

	def before_print(self, settings=None):
		self.print_heading = self.name
		self.sub_heading = ""

	def clear_cache(self):
		dontmanage.cache.delete_keys(UNSEEN_NOTES_KEY)
		return super().clear_cache()

	def mark_seen_by(self, user: str) -> None:
		if user in [d.user for d in self.seen_by]:
			return

		self.append("seen_by", {"user": user})


@dontmanage.whitelist()
def mark_as_seen(note: str):
	note: Note = dontmanage.get_doc("Note", note)
	note.mark_seen_by(dontmanage.session.user)
	note.save(ignore_permissions=True, ignore_version=True)


def get_permission_query_conditions(user):
	if not user:
		user = dontmanage.session.user

	return f"(`tabNote`.owner = {dontmanage.db.escape(user)} or `tabNote`.public = 1)"


def has_permission(doc, user):
	return bool(doc.public or doc.owner == user)


def get_unseen_notes():
	return (
		dontmanage.cache.get_value(
			f"{UNSEEN_NOTES_KEY}{dontmanage.session.user}",
		)
		or []
	)


@dontmanage.whitelist()
def reset_notes():
	dontmanage.cache.set_value(f"{UNSEEN_NOTES_KEY}{dontmanage.session.user}", [])
	return dontmanage.cache.get_value(f"{UNSEEN_NOTES_KEY}{dontmanage.session.user}")


def _get_unseen_notes():
	from dontmanage.query_builder.terms import ParameterizedValueWrapper, SubQuery

	note = dontmanage.qb.DocType("Note")
	nsb = dontmanage.qb.DocType("Note Seen By").as_("nsb")

	results = (
		dontmanage.qb.from_(note)
		.select(note.name, note.title, note.content, note.notify_on_every_login)
		.where(
			(note.notify_on_login == 1)
			& (note.expire_notification_on > dontmanage.utils.now())
			& (
				ParameterizedValueWrapper(dontmanage.session.user).notin(
					SubQuery(dontmanage.qb.from_(nsb).select(nsb.user).where(nsb.parent == note.name))
				)
			)
		)
	).run(as_dict=1)
	dontmanage.cache.set_value(f"{UNSEEN_NOTES_KEY}{dontmanage.session.user}", results)
