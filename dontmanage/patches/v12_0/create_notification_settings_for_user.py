import dontmanage
from dontmanage.desk.doctype.notification_settings.notification_settings import (
	create_notification_settings,
)


def execute():
	dontmanage.reload_doc("desk", "doctype", "notification_settings")
	dontmanage.reload_doc("desk", "doctype", "notification_subscribed_document")

	users = dontmanage.get_all("User", fields=["name"])
	for user in users:
		create_notification_settings(user.name)
