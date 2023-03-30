# Copyright (c) 2018, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	signatures = dontmanage.db.get_list(
		"User", {"email_signature": ["!=", ""]}, ["name", "email_signature"]
	)
	dontmanage.reload_doc("core", "doctype", "user")
	for d in signatures:
		signature = d.get("email_signature")
		signature = signature.replace("\n", "<br>")
		signature = "<div>" + signature + "</div>"
		dontmanage.db.set_value("User", d.get("name"), "email_signature", signature)
