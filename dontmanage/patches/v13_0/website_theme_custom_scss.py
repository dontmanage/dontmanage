import dontmanage


def execute():
	dontmanage.reload_doc("website", "doctype", "website_theme_ignore_app")
	dontmanage.reload_doc("website", "doctype", "color")
	dontmanage.reload_doc("website", "doctype", "website_theme", force=True)

	for theme in dontmanage.get_all("Website Theme"):
		doc = dontmanage.get_doc("Website Theme", theme.name)
		if not doc.get("custom_scss") and doc.theme_scss:
			# move old theme to new theme
			doc.custom_scss = doc.theme_scss

			if doc.background_color:
				setup_color_record(doc.background_color)

			doc.save()


def setup_color_record(color):
	dontmanage.get_doc(
		{
			"doctype": "Color",
			"__newname": color,
			"color": color,
		}
	).save()
