# Copyright (c) 2021, DontManage and Contributors
# MIT License. See LICENSE


import dontmanage
import dontmanage.utils
from dontmanage import _
from dontmanage.email.doctype.email_group.email_group import add_subscribers
from dontmanage.rate_limiter import rate_limit
from dontmanage.utils.safe_exec import is_job_queued
from dontmanage.utils.verified_command import get_signed_params, verify_request
from dontmanage.website.website_generator import WebsiteGenerator

from .exceptions import NewsletterAlreadySentError, NewsletterNotSavedError, NoRecipientFoundError


class Newsletter(WebsiteGenerator):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.email.doctype.newsletter_attachment.newsletter_attachment import NewsletterAttachment
		from dontmanage.email.doctype.newsletter_email_group.newsletter_email_group import (
			NewsletterEmailGroup,
		)
		from dontmanage.types import DF

		attachments: DF.Table[NewsletterAttachment]
		campaign: DF.Link | None
		content_type: DF.Literal["Rich Text", "Markdown", "HTML"]
		email_group: DF.Table[NewsletterEmailGroup]
		email_sent: DF.Check
		email_sent_at: DF.Datetime | None
		message: DF.TextEditor | None
		message_html: DF.HTMLEditor | None
		message_md: DF.MarkdownEditor | None
		published: DF.Check
		route: DF.Data | None
		schedule_send: DF.Datetime | None
		schedule_sending: DF.Check
		scheduled_to_send: DF.Int
		send_from: DF.Data | None
		send_unsubscribe_link: DF.Check
		send_webview_link: DF.Check
		sender_email: DF.Data
		sender_name: DF.Data | None
		subject: DF.SmallText
		total_recipients: DF.Int
		total_views: DF.Int
	# end: auto-generated types

	def validate(self):
		self.route = f"newsletters/{self.name}"
		self.validate_sender_address()
		self.validate_publishing()
		self.validate_scheduling_date()

	@property
	def newsletter_recipients(self) -> list[str]:
		if getattr(self, "_recipients", None) is None:
			self._recipients = self.get_recipients()
		return self._recipients

	@dontmanage.whitelist()
	def get_sending_status(self):
		count_by_status = dontmanage.get_all(
			"Email Queue",
			filters={"reference_doctype": self.doctype, "reference_name": self.name},
			fields=["status", "count(name) as count"],
			group_by="status",
			order_by="status",
		)
		sent = 0
		error = 0
		total = 0
		for row in count_by_status:
			if row.status == "Sent":
				sent = row.count
			elif row.status == "Error":
				error = row.count
			total += row.count
		emails_queued = is_job_queued(
			job_name=dontmanage.utils.get_job_name("send_bulk_emails_for", self.doctype, self.name),
			queue="long",
		)
		return {"sent": sent, "error": error, "total": total, "emails_queued": emails_queued}

	@dontmanage.whitelist()
	def send_test_email(self, email):
		test_emails = dontmanage.utils.validate_email_address(email, throw=True)
		self.send_newsletter(emails=test_emails, test_email=True)
		dontmanage.msgprint(_("Test email sent to {0}").format(email), alert=True)

	@dontmanage.whitelist()
	def find_broken_links(self):
		import requests
		from bs4 import BeautifulSoup

		html = self.get_message()
		soup = BeautifulSoup(html, "html.parser")
		links = soup.find_all("a")
		images = soup.find_all("img")
		broken_links = []
		for el in links + images:
			url = el.attrs.get("href") or el.attrs.get("src")
			try:
				response = requests.head(url, verify=False, timeout=5)
				if response.status_code >= 400:
					broken_links.append(url)
			except Exception:
				broken_links.append(url)
		return broken_links

	@dontmanage.whitelist()
	def send_emails(self):
		"""queue sending emails to recipients"""
		self.schedule_sending = False
		self.schedule_send = None
		self.queue_all()

	def validate_send(self):
		"""Validate if Newsletter can be sent."""
		self.validate_newsletter_status()
		self.validate_newsletter_recipients()

	def validate_newsletter_status(self):
		if self.email_sent:
			dontmanage.throw(_("Newsletter has already been sent"), exc=NewsletterAlreadySentError)

		if self.get("__islocal"):
			dontmanage.throw(_("Please save the Newsletter before sending"), exc=NewsletterNotSavedError)

	def validate_newsletter_recipients(self):
		if not self.newsletter_recipients:
			dontmanage.throw(_("Newsletter should have atleast one recipient"), exc=NoRecipientFoundError)

	def validate_sender_address(self):
		"""Validate self.send_from is a valid email address or not."""
		if self.sender_email:
			dontmanage.utils.validate_email_address(self.sender_email, throw=True)
			self.send_from = (
				f"{self.sender_name} <{self.sender_email}>" if self.sender_name else self.sender_email
			)

	def validate_publishing(self):
		if self.send_webview_link and not self.published:
			dontmanage.throw(_("Newsletter must be published to send webview link in email"))

	def validate_scheduling_date(self):
		if (
			self.schedule_sending
			and dontmanage.utils.get_datetime(self.schedule_send) < dontmanage.utils.now_datetime()
		):
			dontmanage.throw(_("Past dates are not allowed for Scheduling."))

	def get_linked_email_queue(self) -> list[str]:
		"""Get list of email queue linked to this newsletter."""
		return dontmanage.get_all(
			"Email Queue",
			filters={
				"reference_doctype": self.doctype,
				"reference_name": self.name,
			},
			pluck="name",
		)

	def get_queued_recipients(self) -> list[str]:
		"""Recipients who have already been queued for receiving the newsletter."""
		return dontmanage.get_all(
			"Email Queue Recipient",
			filters={
				"parent": ("in", self.get_linked_email_queue()),
			},
			pluck="recipient",
		)

	def get_pending_recipients(self) -> list[str]:
		"""Get list of pending recipients of the newsletter. These
		recipients may not have receive the newsletter in the previous iteration.
		"""

		queued_recipients = set(self.get_queued_recipients())
		return [x for x in self.newsletter_recipients if x not in queued_recipients]

	def queue_all(self):
		"""Queue Newsletter to all the recipients generated from the `Email Group` table"""
		self.validate()
		self.validate_send()

		recipients = self.get_pending_recipients()
		self.send_newsletter(emails=recipients)

		self.email_sent = True
		self.email_sent_at = dontmanage.utils.now()
		self.total_recipients = len(recipients)
		self.save()

	def get_newsletter_attachments(self) -> list[dict[str, str]]:
		"""Get list of attachments on current Newsletter"""
		return [{"file_url": row.attachment} for row in self.attachments]

	def send_newsletter(self, emails: list[str], test_email: bool = False):
		"""Trigger email generation for `emails` and add it in Email Queue."""
		attachments = self.get_newsletter_attachments()
		sender = self.send_from or dontmanage.utils.get_formatted_email(self.owner)
		args = self.as_dict()
		args["message"] = self.get_message(medium="email")

		is_auto_commit_set = bool(dontmanage.db.auto_commit_on_many_writes)
		dontmanage.db.auto_commit_on_many_writes = not dontmanage.flags.in_test

		dontmanage.sendmail(
			subject=self.subject,
			sender=sender,
			recipients=emails,
			attachments=attachments,
			template="newsletter",
			add_unsubscribe_link=self.send_unsubscribe_link,
			unsubscribe_method="/unsubscribe",
			unsubscribe_params={"name": self.name},
			reference_doctype=self.doctype,
			reference_name=self.name,
			queue_separately=True,
			send_priority=0,
			args=args,
			email_read_tracker_url=None
			if test_email
			else "/api/method/dontmanage.email.doctype.newsletter.newsletter.newsletter_email_read",
		)

		dontmanage.db.auto_commit_on_many_writes = is_auto_commit_set

	def get_message(self, medium=None) -> str:
		message = self.message
		if self.content_type == "Markdown":
			message = dontmanage.utils.md_to_html(self.message_md)
		if self.content_type == "HTML":
			message = self.message_html

		html = dontmanage.render_template(message, {"doc": self.as_dict()})

		return self.add_source(html, medium=medium)

	def add_source(self, html: str, medium="None") -> str:
		"""Add source to the site links in the newsletter content."""
		from bs4 import BeautifulSoup

		soup = BeautifulSoup(html, "html.parser")

		links = soup.find_all("a")
		for link in links:
			href = link.get("href")
			if href and not href.startswith("#"):
				if not dontmanage.utils.is_site_link(href):
					continue
				new_href = dontmanage.utils.add_trackers_to_url(
					href, source="Newsletter", campaign=self.campaign, medium=medium
				)
				link["href"] = new_href

		return str(soup)

	def get_recipients(self) -> list[str]:
		"""Get recipients from Email Group"""
		emails = dontmanage.get_all(
			"Email Group Member",
			filters={"unsubscribed": 0, "email_group": ("in", self.get_email_groups())},
			pluck="email",
		)
		return list(set(emails))

	def get_email_groups(self) -> list[str]:
		# wondering why the 'or'? i can't figure out why both aren't equivalent - @gavin
		return [x.email_group for x in self.email_group] or dontmanage.get_all(
			"Newsletter Email Group",
			filters={"parent": self.name, "parenttype": "Newsletter"},
			pluck="email_group",
		)

	def get_attachments(self) -> list[dict[str, str]]:
		return dontmanage.get_all(
			"File",
			fields=["name", "file_name", "file_url", "is_private"],
			filters={
				"attached_to_name": self.name,
				"attached_to_doctype": "Newsletter",
				"is_private": 0,
			},
		)


def confirmed_unsubscribe(email, group):
	"""unsubscribe the email(user) from the mailing list(email_group)"""
	dontmanage.flags.ignore_permissions = True
	doc = dontmanage.get_doc("Email Group Member", {"email": email, "email_group": group})
	if not doc.unsubscribed:
		doc.unsubscribed = 1
		doc.save(ignore_permissions=True)


@dontmanage.whitelist(allow_guest=True)
@rate_limit(limit=10, seconds=60 * 60)
def subscribe(email, email_group=None):
	"""API endpoint to subscribe an email to a particular email group. Triggers a confirmation email."""

	if email_group is None:
		email_group = get_default_email_group()

	# build subscription confirmation URL
	api_endpoint = dontmanage.utils.get_url(
		"/api/method/dontmanage.email.doctype.newsletter.newsletter.confirm_subscription"
	)
	signed_params = get_signed_params({"email": email, "email_group": email_group})
	confirm_subscription_url = f"{api_endpoint}?{signed_params}"

	# fetch custom template if available
	email_confirmation_template = dontmanage.db.get_value(
		"Email Group", email_group, "confirmation_email_template"
	)

	# build email and send
	if email_confirmation_template:
		args = {"email": email, "confirmation_url": confirm_subscription_url, "email_group": email_group}
		email_template = dontmanage.get_doc("Email Template", email_confirmation_template)
		email_subject = email_template.subject
		content = dontmanage.render_template(email_template.response, args)
	else:
		email_subject = _("Confirm Your Email")
		translatable_content = (
			_("Thank you for your interest in subscribing to our updates"),
			_("Please verify your Email Address"),
			confirm_subscription_url,
			_("Click here to verify"),
		)
		content = """
			<p>{}. {}.</p>
			<p><a href="{}">{}</a></p>
		""".format(*translatable_content)

	dontmanage.sendmail(
		email,
		subject=email_subject,
		content=content,
	)


@dontmanage.whitelist(allow_guest=True)
def confirm_subscription(email, email_group=None):
	"""API endpoint to confirm email subscription.
	This endpoint is called when user clicks on the link sent to their mail.
	"""
	if not verify_request():
		return

	if email_group is None:
		email_group = get_default_email_group()

	try:
		group = dontmanage.get_doc("Email Group", email_group)
	except dontmanage.DoesNotExistError:
		group = dontmanage.get_doc({"doctype": "Email Group", "title": email_group}).insert(
			ignore_permissions=True
		)

	dontmanage.flags.ignore_permissions = True

	add_subscribers(email_group, email)
	dontmanage.db.commit()

	welcome_url = group.get_welcome_url(email)

	if welcome_url:
		dontmanage.local.response["type"] = "redirect"
		dontmanage.local.response["location"] = welcome_url
	else:
		dontmanage.respond_as_web_page(
			_("Confirmed"),
			_("{0} has been successfully added to the Email Group.").format(email),
			indicator_color="green",
		)


def get_list_context(context=None):
	context.update(
		{
			"show_search": True,
			"no_breadcrumbs": True,
			"title": _("Newsletters"),
			"filters": {"published": 1},
			"row_template": "email/doctype/newsletter/templates/newsletter_row.html",
		}
	)


def send_scheduled_email():
	"""Send scheduled newsletter to the recipients."""
	scheduled_newsletter = dontmanage.get_all(
		"Newsletter",
		filters={
			"schedule_send": ("<=", dontmanage.utils.now_datetime()),
			"email_sent": False,
			"schedule_sending": True,
		},
		ignore_ifnull=True,
		pluck="name",
	)

	for newsletter_name in scheduled_newsletter:
		try:
			newsletter = dontmanage.get_doc("Newsletter", newsletter_name)
			newsletter.queue_all()

		except Exception:
			dontmanage.db.rollback()

			# wasn't able to send emails :(
			dontmanage.db.set_value("Newsletter", newsletter_name, "email_sent", 0)
			newsletter.log_error("Failed to send newsletter")

		if not dontmanage.flags.in_test:
			dontmanage.db.commit()


@dontmanage.whitelist(allow_guest=True)
def newsletter_email_read(recipient_email=None, reference_doctype=None, reference_name=None):
	if not (recipient_email and reference_name):
		return
	verify_request()
	try:
		doc = dontmanage.get_cached_doc("Newsletter", reference_name)
		if doc.add_viewed(recipient_email, force=True, unique_views=True):
			newsletter = dontmanage.qb.DocType("Newsletter")
			(
				dontmanage.qb.update(newsletter)
				.set(newsletter.total_views, newsletter.total_views + 1)
				.where(newsletter.name == doc.name)
			).run()

	except Exception:
		doc.log_error(f"Unable to mark as viewed for {recipient_email}")

	finally:
		dontmanage.response.update(dontmanage.utils.get_imaginary_pixel_response())


def get_default_email_group():
	return _("Website", lang=dontmanage.db.get_default("language"))
