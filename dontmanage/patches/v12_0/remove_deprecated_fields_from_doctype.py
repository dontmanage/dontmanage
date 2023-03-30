import dontmanage


def execute():
	dontmanage.reload_doc("core", "doctype", "doctype_link")
	dontmanage.reload_doc("core", "doctype", "doctype_action")
	dontmanage.reload_doc("core", "doctype", "doctype")
	dontmanage.model.delete_fields(
		{"DocType": ["hide_heading", "image_view", "read_only_onload"]}, delete=1
	)

	dontmanage.db.delete("Property Setter", {"property": "read_only_onload"})
