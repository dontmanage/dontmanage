# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def get_notification_config():
	return {
		"for_doctype": {
			"Error Log": {"seen": 0},
			"Communication": {"status": "Open", "communication_type": "Communication"},
			"ToDo": "dontmanage.core.notifications.get_things_todo",
			"Event": "dontmanage.core.notifications.get_todays_events",
			"Error Snapshot": {"seen": 0, "parent_error_snapshot": None},
			"Workflow Action": {"status": "Open"},
		},
	}


def get_things_todo(as_list=False):
	"""Returns a count of incomplete todos"""
	data = dontmanage.get_list(
		"ToDo",
		fields=["name", "description"] if as_list else "count(*)",
		filters=[["ToDo", "status", "=", "Open"]],
		or_filters=[
			["ToDo", "allocated_to", "=", dontmanage.session.user],
			["ToDo", "assigned_by", "=", dontmanage.session.user],
		],
		as_list=True,
	)

	if as_list:
		return data
	else:
		return data[0][0]


def get_todays_events(as_list=False):
	"""Returns a count of todays events in calendar"""
	from dontmanage.desk.doctype.event.event import get_events
	from dontmanage.utils import nowdate

	today = nowdate()
	events = get_events(today, today)
	return events if as_list else len(events)
