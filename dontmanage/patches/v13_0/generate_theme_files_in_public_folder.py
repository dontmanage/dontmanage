# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.reload_doc("website", "doctype", "website_theme_ignore_app")
	themes = dontmanage.get_all(
		"Website Theme", filters={"theme_url": ("not like", "/files/website_theme/%")}
	)
	for theme in themes:
		doc = dontmanage.get_doc("Website Theme", theme.name)
		try:
			doc.generate_bootstrap_theme()
			doc.save()
		except Exception:
			print("Ignoring....")
			print(dontmanage.get_traceback())
