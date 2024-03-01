import dontmanage


def execute():
	Event = dontmanage.qb.DocType("Event")
	query = (
		dontmanage.qb.update(Event)
		.set(Event.event_type, "Private")
		.set(Event.status, "Cancelled")
		.where(Event.event_type == "Cancelled")
	)
	query.run()
