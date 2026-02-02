import dontmanage


def execute():
	desktop_icons = dontmanage.get_all(
		"Desktop Icon",
		filters={
			"icon_type": "Link",
			"link_type": ["in", ["Workspace", "DocType"]],
		},
	)

	for icon in desktop_icons:
		icon_doc = dontmanage.get_doc("Desktop Icon", icon.name)
		if dontmanage.db.exists("Workspace Sidebar", icon.name):
			icon_doc.link_type = "Workspace Sidebar"
			icon_doc.link_to = icon.name
			icon_doc.save()

	dontmanage.db.commit()
