import dontmanage


def execute():
	dontmanage.db.set_single_value(
		"System Settings",
		{"document_share_key_expiry": 30},
	)
