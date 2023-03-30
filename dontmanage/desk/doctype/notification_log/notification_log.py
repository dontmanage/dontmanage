# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.desk.doctype.notification_settings.notification_settings import (
	is_email_notifications_enabled_for_type,
	is_notifications_enabled,
)
from dontmanage.model.document import Document


class NotificationLog(Document):
	def after_insert(self):
		dontmanage.publish_realtime("notification", after_commit=True, user=self.for_user)
		set_notifications_as_unseen(self.for_user)
		if is_email_notifications_enabled_for_type(self.for_user, self.type):
			try:
				send_notification_email(self)
			except dontmanage.OutgoingEmailError:
				self.log_error(_("Failed to send notification email"))

	@staticmethod
	def clear_old_logs(days=180):
		from dontmanage.query_builder import Interval
		from dontmanage.query_builder.functions import Now

		table = dontmanage.qb.DocType("Notification Log")
		dontmanage.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))


def get_permission_query_conditions(for_user):
	if not for_user:
		for_user = dontmanage.session.user

	if for_user == "Administrator":
		return

	return f"""(`tabNotification Log`.for_user = {dontmanage.db.escape(for_user)})"""


def get_title(doctype, docname, title_field=None):
	if not title_field:
		title_field = dontmanage.get_meta(doctype).get_title_field()
	title = docname if title_field == "name" else dontmanage.db.get_value(doctype, docname, title_field)
	return title


def get_title_html(title):
	return f'<b class="subject-title">{title}</b>'


def enqueue_create_notification(users: list[str] | str, doc: dict):
	"""Send notification to users.

	users: list of user emails or string of users with comma separated emails
	doc: contents of `Notification` doc
	"""

	# During installation of new site, enqueue_create_notification tries to connect to Redis.
	# This breaks new site creation if Redis server is not running.
	# We do not need any notifications in fresh installation
	if dontmanage.flags.in_install:
		return

	doc = dontmanage._dict(doc)

	if isinstance(users, str):
		users = [user.strip() for user in users.split(",") if user.strip()]
	users = list(set(users))

	dontmanage.enqueue(
		"dontmanage.desk.doctype.notification_log.notification_log.make_notification_logs",
		doc=doc,
		users=users,
		now=dontmanage.flags.in_test,
	)


def make_notification_logs(doc, users):
	for user in _get_user_ids(users):
		notification = dontmanage.new_doc("Notification Log")
		notification.update(doc)
		notification.for_user = user
		if (
			notification.for_user != notification.from_user
			or doc.type == "Energy Point"
			or doc.type == "Alert"
		):
			notification.insert(ignore_permissions=True)


def _get_user_ids(user_emails):
	user_names = dontmanage.db.get_values(
		"User", {"enabled": 1, "email": ("in", user_emails)}, "name", pluck=True
	)
	return [user for user in user_names if is_notifications_enabled(user)]


def send_notification_email(doc):

	if doc.type == "Energy Point" and doc.email_content is None:
		return

	from dontmanage.utils import get_url_to_form, strip_html

	email = dontmanage.db.get_value("User", doc.for_user, "email")
	if not email:
		return

	doc_link = get_url_to_form(doc.document_type, doc.document_name)
	header = get_email_header(doc)
	email_subject = strip_html(doc.subject)

	dontmanage.sendmail(
		recipients=email,
		subject=email_subject,
		template="new_notification",
		args={
			"body_content": doc.subject,
			"description": doc.email_content,
			"document_type": doc.document_type,
			"document_name": doc.document_name,
			"doc_link": doc_link,
		},
		header=[header, "orange"],
		now=dontmanage.flags.in_test,
	)


def get_email_header(doc):
	docname = doc.document_name
	header_map = {
		"Default": _("New Notification"),
		"Mention": _("New Mention on {0}").format(docname),
		"Assignment": _("Assignment Update on {0}").format(docname),
		"Share": _("New Document Shared {0}").format(docname),
		"Energy Point": _("Energy Point Update on {0}").format(docname),
	}

	return header_map[doc.type or "Default"]


@dontmanage.whitelist()
def get_notification_logs(limit=20):
	notification_logs = dontmanage.db.get_list(
		"Notification Log", fields=["*"], limit=limit, order_by="modified desc"
	)

	users = [log.from_user for log in notification_logs]
	users = [*set(users)]  # remove duplicates
	user_info = dontmanage._dict()

	for user in users:
		dontmanage.utils.add_user_info(user, user_info)

	return {"notification_logs": notification_logs, "user_info": user_info}


@dontmanage.whitelist()
def mark_all_as_read():
	unread_docs_list = dontmanage.get_all(
		"Notification Log", filters={"read": 0, "for_user": dontmanage.session.user}
	)
	unread_docnames = [doc.name for doc in unread_docs_list]
	if unread_docnames:
		filters = {"name": ["in", unread_docnames]}
		dontmanage.db.set_value("Notification Log", filters, "read", 1, update_modified=False)


@dontmanage.whitelist()
def mark_as_read(docname):
	if docname:
		dontmanage.db.set_value("Notification Log", docname, "read", 1, update_modified=False)


@dontmanage.whitelist()
def trigger_indicator_hide():
	dontmanage.publish_realtime("indicator_hide", user=dontmanage.session.user)


def set_notifications_as_unseen(user):
	try:
		dontmanage.db.set_value("Notification Settings", user, "seen", 0, update_modified=False)
	except dontmanage.DoesNotExistError:
		return
