import dontmanage


def execute():
	doctype = "Integration Request"

	if not dontmanage.db.has_column(doctype, "integration_type"):
		return

	dontmanage.db.set_value(
		doctype,
		{"integration_type": "Remote", "integration_request_service": ("!=", "PayPal")},
		"is_remote_request",
		1,
	)
	dontmanage.db.set_value(
		doctype,
		{"integration_type": "Subscription Notification"},
		"request_description",
		"Subscription Notification",
	)
