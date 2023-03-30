# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():

	dontmanage.reload_doc("Email", "doctype", "Notification")

	notifications = dontmanage.get_all("Notification", {"is_standard": 1}, {"name", "channel"})
	for notification in notifications:
		if not notification.channel:
			dontmanage.db.set_value(
				"Notification", notification.name, "channel", "Email", update_modified=False
			)
			dontmanage.db.commit()
