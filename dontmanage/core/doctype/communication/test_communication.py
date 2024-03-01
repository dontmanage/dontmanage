# Copyright (c) 2022, DontManage and Contributors
# License: MIT. See LICENSE
from typing import TYPE_CHECKING
from urllib.parse import quote

import dontmanage
from dontmanage.core.doctype.communication.communication import Communication, get_emails
from dontmanage.email.doctype.email_queue.email_queue import EmailQueue
from dontmanage.tests.utils import DontManageTestCase

if TYPE_CHECKING:
	from dontmanage.contacts.doctype.contact.contact import Contact
	from dontmanage.email.doctype.email_account.email_account import EmailAccount

test_records = dontmanage.get_test_records("Communication")


class TestCommunication(DontManageTestCase):
	def test_email(self):
		valid_email_list = [
			"Full Name <full@example.com>",
			'"Full Name with quotes and <weird@chars.com>" <weird@example.com>',
			"Surname, Name <name.surname@domain.com>",
			"Purchase@ABC <purchase@abc.com>",
			"xyz@abc2.com <xyz@abc.com>",
			"Name [something else] <name@domain.com>",
		]

		invalid_email_list = [
			"[invalid!email]",
			"invalid-email",
			"tes2",
			"e",
			"rrrrrrrr",
			"manas",
			"[[[sample]]]",
			"[invalid!email].com",
		]

		for i, x in enumerate(valid_email_list):
			with self.subTest(i=i, x=x):
				self.assertTrue(dontmanage.utils.parse_addr(x)[1])

		for i, x in enumerate(invalid_email_list):
			with self.subTest(i=i, x=x):
				self.assertFalse(dontmanage.utils.parse_addr(x)[0])

	def test_name(self):
		valid_email_list = [
			"Full Name <full@example.com>",
			'"Full Name with quotes and <weird@chars.com>" <weird@example.com>',
			"Surname, Name <name.surname@domain.com>",
			"Purchase@ABC <purchase@abc.com>",
			"xyz@abc2.com <xyz@abc.com>",
			"Name [something else] <name@domain.com>",
		]

		invalid_email_list = [
			"[invalid!email]",
			"invalid-email",
			"tes2",
			"e",
			"rrrrrrrr",
			"manas",
			"[[[sample]]]",
			"[invalid!email].com",
		]

		for x in valid_email_list:
			self.assertTrue(dontmanage.utils.parse_addr(x)[0])

		for x in invalid_email_list:
			self.assertFalse(dontmanage.utils.parse_addr(x)[0])

	def test_circular_linking(self):
		a = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"content": "This was created to test circular linking: Communication A",
			}
		).insert(ignore_permissions=True)

		b = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"content": "This was created to test circular linking: Communication B",
				"reference_doctype": "Communication",
				"reference_name": a.name,
			}
		).insert(ignore_permissions=True)

		c = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"content": "This was created to test circular linking: Communication C",
				"reference_doctype": "Communication",
				"reference_name": b.name,
			}
		).insert(ignore_permissions=True)

		a = dontmanage.get_doc("Communication", a.name)
		a.reference_doctype = "Communication"
		a.reference_name = c.name

		self.assertRaises(dontmanage.CircularLinkingError, a.save)

	def test_deduplication_timeline_links(self):
		dontmanage.delete_doc_if_exists("Note", "deduplication timeline links")

		note = dontmanage.get_doc(
			{
				"doctype": "Note",
				"title": "deduplication timeline links",
				"content": "deduplication timeline links",
			}
		).insert(ignore_permissions=True)

		comm = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"content": "Deduplication of Links",
				"communication_medium": "Email",
			}
		).insert(ignore_permissions=True)

		# adding same link twice
		comm.add_link(link_doctype="Note", link_name=note.name, autosave=True)
		comm.add_link(link_doctype="Note", link_name=note.name, autosave=True)

		comm = dontmanage.get_doc("Communication", comm.name)

		self.assertNotEqual(2, len(comm.timeline_links))

	def test_contacts_attached(self):
		contact_sender: "Contact" = dontmanage.get_doc(
			{
				"doctype": "Contact",
				"first_name": "contact_sender",
			}
		)
		contact_sender.add_email("comm_sender@example.com")
		contact_sender.insert(ignore_permissions=True)

		contact_recipient: "Contact" = dontmanage.get_doc(
			{
				"doctype": "Contact",
				"first_name": "contact_recipient",
			}
		)
		contact_recipient.add_email("comm_recipient@example.com")
		contact_recipient.insert(ignore_permissions=True)

		contact_cc: "Contact" = dontmanage.get_doc(
			{
				"doctype": "Contact",
				"first_name": "contact_cc",
			}
		)
		contact_cc.add_email("comm_cc@example.com")
		contact_cc.insert(ignore_permissions=True)

		comm: Communication = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_medium": "Email",
				"subject": "Contacts Attached Test",
				"sender": "comm_sender@example.com",
				"recipients": "comm_recipient@example.com",
				"cc": "comm_cc@example.com",
			}
		).insert(ignore_permissions=True)

		comm = dontmanage.get_doc("Communication", comm.name)
		contact_links = [x.link_name for x in comm.timeline_links]

		self.assertIn(contact_sender.name, contact_links)
		self.assertIn(contact_recipient.name, contact_links)
		self.assertIn(contact_cc.name, contact_links)

	def test_get_communication_data(self):
		from dontmanage.desk.form.load import get_communication_data

		dontmanage.delete_doc_if_exists("Note", "get communication data")

		note = dontmanage.get_doc(
			{"doctype": "Note", "title": "get communication data", "content": "get communication data"}
		).insert(ignore_permissions=True)

		comm_note_1 = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"content": "Test Get Communication Data 1",
				"communication_medium": "Email",
			}
		).insert(ignore_permissions=True)

		comm_note_1.add_link(link_doctype="Note", link_name=note.name, autosave=True)

		comm_note_2 = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"content": "Test Get Communication Data 2",
				"communication_medium": "Email",
			}
		).insert(ignore_permissions=True)

		comm_note_2.add_link(link_doctype="Note", link_name=note.name, autosave=True)

		comms = get_communication_data("Note", note.name, as_dict=True)

		data = [comm.name for comm in comms]
		self.assertIn(comm_note_1.name, data)
		self.assertIn(comm_note_2.name, data)

	def test_link_in_email(self):
		create_email_account()

		notes = {}
		for i in range(2):
			dontmanage.delete_doc_if_exists("Note", f"test document link in email {i}")
			notes[i] = dontmanage.get_doc(
				{
					"doctype": "Note",
					"title": f"test document link in email {i}",
				}
			).insert(ignore_permissions=True)

		comm = dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_medium": "Email",
				"subject": "Document Link in Email",
				"sender": "comm_sender@example.com",
				"recipients": f'comm_recipient+{quote("Note")}+{quote(notes[0].name)}@example.com,comm_recipient+{quote("Note")}={quote(notes[1].name)}@example.com',
			}
		).insert(ignore_permissions=True)

		doc_links = [
			(timeline_link.link_doctype, timeline_link.link_name) for timeline_link in comm.timeline_links
		]
		self.assertIn(("Note", notes[0].name), doc_links)
		self.assertIn(("Note", notes[1].name), doc_links)

	def test_parse_emails(self):
		emails = get_emails(
			[
				"comm_recipient+DocType+DocName@example.com",
				'"First, LastName" <first.lastname@email.com>',
				"test@user.com",
			]
		)

		self.assertEqual(emails[0], "comm_recipient+DocType+DocName@example.com")
		self.assertEqual(emails[1], "first.lastname@email.com")
		self.assertEqual(emails[2], "test@user.com")

	def test_signature_in_email_content(self):
		email_account = create_email_account()
		signature = email_account.signature
		base_communication = {
			"doctype": "Communication",
			"communication_medium": "Email",
			"subject": "Document Link in Email",
			"sender": "comm_sender@example.com",
		}
		comm_with_signature = dontmanage.get_doc(
			base_communication
			| {
				"content": f"""<div class="ql-editor read-mode">
				Hi,
				How are you?
				</div><p></p><br><p class="signature">{signature}</p>""",
			}
		).insert(ignore_permissions=True)
		comm_without_signature = dontmanage.get_doc(
			base_communication
			| {
				"content": """<div class="ql-editor read-mode">
				Hi,
				How are you?
				</div>"""
			}
		).insert(ignore_permissions=True)

		self.assertEqual(comm_with_signature.content, comm_without_signature.content)
		self.assertEqual(comm_with_signature.content.count(signature), 1)
		self.assertEqual(comm_without_signature.content.count(signature), 1)


class TestCommunicationEmailMixin(DontManageTestCase):
	def new_communication(self, recipients=None, cc=None, bcc=None) -> Communication:
		recipients = ", ".join(recipients or [])
		cc = ", ".join(cc or [])
		bcc = ", ".join(bcc or [])

		return dontmanage.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"content": "Test content",
				"recipients": recipients,
				"cc": cc,
				"bcc": bcc,
			}
		).insert(ignore_permissions=True)

	def new_user(self, email, **user_data):
		user_data.setdefault("first_name", "first_name")
		user = dontmanage.new_doc("User")
		user.email = email
		user.update(user_data)
		user.insert(ignore_permissions=True, ignore_if_duplicate=True)
		return user

	def test_recipients(self):
		to_list = ["to@test.com", "receiver <to+1@test.com>", "to@test.com"]
		comm = self.new_communication(recipients=to_list)
		res = comm.get_mail_recipients_with_displayname()
		self.assertCountEqual(res, ["to@test.com", "receiver <to+1@test.com>"])
		comm.delete()

	def test_cc(self):
		to_list = ["to@test.com"]
		cc_list = ["cc+1@test.com", "cc <cc+2@test.com>", "to@test.com"]
		user = self.new_user(email="cc+1@test.com", thread_notify=0)
		comm = self.new_communication(recipients=to_list, cc=cc_list)
		res = comm.get_mail_cc_with_displayname()
		self.assertCountEqual(res, ["cc <cc+2@test.com>"])
		user.delete()
		comm.delete()

	def test_bcc(self):
		bcc_list = [
			"bcc+1@test.com",
			"cc <bcc+2@test.com>",
		]
		user = self.new_user(email="bcc+2@test.com", enabled=0)
		comm = self.new_communication(bcc=bcc_list)
		res = comm.get_mail_bcc_with_displayname()
		self.assertCountEqual(res, bcc_list)
		user.delete()
		comm.delete()

	def test_sendmail(self):
		to_list = ["to <to@test.com>"]
		cc_list = ["cc <cc+1@test.com>", "cc <cc+2@test.com>"]

		comm = self.new_communication(recipients=to_list, cc=cc_list)
		comm.send_email()
		doc = EmailQueue.find_one_by_filters(communication=comm.name)
		mail_receivers = [each.recipient for each in doc.recipients]
		self.assertIsNotNone(doc)
		self.assertCountEqual(to_list + cc_list, mail_receivers)
		doc.delete()
		comm.delete()


def create_email_account() -> "EmailAccount":
	dontmanage.delete_doc_if_exists("Email Account", "_Test Comm Account 1")

	dontmanage.flags.mute_emails = False
	dontmanage.flags.sent_mail = None

	return dontmanage.get_doc(
		{
			"is_default": 1,
			"is_global": 1,
			"doctype": "Email Account",
			"domain": "example.com",
			"append_to": "ToDo",
			"email_account_name": "_Test Comm Account 1",
			"enable_outgoing": 1,
			"default_outgoing": 1,
			"smtp_server": "test.example.com",
			"email_id": "test_comm@example.com",
			"password": "password",
			"add_signature": 1,
			"signature": "\nBest Wishes\nTest Signature",
			"enable_auto_reply": 1,
			"auto_reply_message": "",
			"enable_incoming": 1,
			"notify_if_unreplied": 1,
			"unreplied_for_mins": 20,
			"send_notification_to": "test_comm@example.com",
			"pop3_server": "pop.test.example.com",
			"imap_folder": [{"folder_name": "INBOX", "append_to": "ToDo"}],
			"enable_automatic_linking": 1,
		}
	).insert(ignore_permissions=True)