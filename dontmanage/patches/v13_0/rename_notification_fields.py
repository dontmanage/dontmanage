# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.utils.rename_field import rename_field


def execute():
	"""
	Change notification recipient fields from email to receiver fields
	"""
	dontmanage.reload_doc("Email", "doctype", "Notification Recipient")
	dontmanage.reload_doc("Email", "doctype", "Notification")

	rename_field("Notification Recipient", "email_by_document_field", "receiver_by_document_field")
	rename_field("Notification Recipient", "email_by_role", "receiver_by_role")
