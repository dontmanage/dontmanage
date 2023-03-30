# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.utils import now

sitemap = 1


def get_context(context):
	doc = dontmanage.get_doc("Contact Us Settings", "Contact Us Settings")

	if doc.query_options:
		query_options = [opt.strip() for opt in doc.query_options.replace(",", "\n").split("\n") if opt]
	else:
		query_options = ["Sales", "Support", "General"]

	out = {"query_options": query_options, "parents": [{"name": _("Home"), "route": "/"}]}
	out.update(doc.as_dict())

	return out


max_communications_per_hour = 1000


@dontmanage.whitelist(allow_guest=True)
def send_message(subject="Website Query", message="", sender=""):
	if not message:
		dontmanage.response["message"] = "Please write something"
		return

	if not sender:
		dontmanage.response["message"] = "Email Address Required"
		return

	# guest method, cap max writes per hour
	if (
		dontmanage.db.sql(
			"""select count(*) from `tabCommunication`
		where `sent_or_received`="Received"
		and TIMEDIFF(%s, modified) < '01:00:00'""",
			now(),
		)[0][0]
		> max_communications_per_hour
	):
		dontmanage.response[
			"message"
		] = "Sorry: we believe we have received an unreasonably high number of requests of this kind. Please try later"
		return

	# send email
	forward_to_email = dontmanage.db.get_single_value("Contact Us Settings", "forward_to_email")
	if forward_to_email:
		dontmanage.sendmail(recipients=forward_to_email, sender=sender, content=message, subject=subject)

	# add to to-do ?
	dontmanage.get_doc(
		dict(
			doctype="Communication",
			sender=sender,
			subject=_("New Message from Website Contact Page"),
			sent_or_received="Received",
			content=message,
			status="Open",
		)
	).insert(ignore_permissions=True)

	return "okay"
