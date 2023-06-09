import dontmanage


def execute():
	dontmanage.reload_doctype("System Settings")
	doc = dontmanage.get_single("System Settings")
	doc.enable_chat = 1

	# Changes prescribed by Nabin Hait (nabin@dontmanage.io)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_permissions = True

	doc.save()
