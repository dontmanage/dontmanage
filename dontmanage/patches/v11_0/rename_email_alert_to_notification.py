import dontmanage
from dontmanage.model.rename_doc import rename_doc


def execute():
	if dontmanage.db.table_exists("Email Alert Recipient") and not dontmanage.db.table_exists(
		"Notification Recipient"
	):
		rename_doc("DocType", "Email Alert Recipient", "Notification Recipient")
		dontmanage.reload_doc("email", "doctype", "notification_recipient")

	if dontmanage.db.table_exists("Email Alert") and not dontmanage.db.table_exists("Notification"):
		rename_doc("DocType", "Email Alert", "Notification")
		dontmanage.reload_doc("email", "doctype", "notification")
