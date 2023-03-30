# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import os

import dontmanage
from dontmanage.core.doctype.data_import.data_import import export_json, import_doc


def sync_fixtures(app=None):
	"""Import, overwrite fixtures from `[app]/fixtures`"""
	if app:
		apps = [app]
	else:
		apps = dontmanage.get_installed_apps()

	dontmanage.flags.in_fixtures = True

	for app in apps:
		fixtures_path = dontmanage.get_app_path(app, "fixtures")
		if os.path.exists(fixtures_path):
			import_doc(fixtures_path)

		import_custom_scripts(app)

	dontmanage.flags.in_fixtures = False


def import_custom_scripts(app):
	"""Import custom scripts from `[app]/fixtures/custom_scripts`"""
	if os.path.exists(dontmanage.get_app_path(app, "fixtures", "custom_scripts")):
		for fname in os.listdir(dontmanage.get_app_path(app, "fixtures", "custom_scripts")):
			if fname.endswith(".js"):
				with open(dontmanage.get_app_path(app, "fixtures", "custom_scripts") + os.path.sep + fname) as f:
					doctype = fname.rsplit(".", 1)[0]
					script = f.read()
					if dontmanage.db.exists("Client Script", {"dt": doctype}):
						custom_script = dontmanage.get_doc("Client Script", {"dt": doctype})
						custom_script.script = script
						custom_script.save()
					else:
						dontmanage.get_doc({"doctype": "Client Script", "dt": doctype, "script": script}).insert()


def export_fixtures(app=None):
	"""Export fixtures as JSON to `[app]/fixtures`"""
	if app:
		apps = [app]
	else:
		apps = dontmanage.get_installed_apps()
	for app in apps:
		for fixture in dontmanage.get_hooks("fixtures", app_name=app):
			filters = None
			or_filters = None
			if isinstance(fixture, dict):
				filters = fixture.get("filters")
				or_filters = fixture.get("or_filters")
				fixture = fixture.get("doctype") or fixture.get("dt")
			print(f"Exporting {fixture} app {app} filters {(filters if filters else or_filters)}")
			if not os.path.exists(dontmanage.get_app_path(app, "fixtures")):
				os.mkdir(dontmanage.get_app_path(app, "fixtures"))

			export_json(
				fixture,
				dontmanage.get_app_path(app, "fixtures", dontmanage.scrub(fixture) + ".json"),
				filters=filters,
				or_filters=or_filters,
				order_by="idx asc, creation asc",
			)
