import dontmanage
from dontmanage.model.sync import check_if_record_exists


def execute():
	for sidebar in dontmanage.get_all("Workspace Sidebar", pluck="name"):
		sidebar_doc = dontmanage.get_doc("Workspace Sidebar", sidebar)

		if sidebar_doc.app and check_if_record_exists(
			"app",
			dontmanage.get_app_path(sidebar_doc.app),
			"Workspace Sidebar",
			sidebar_doc.name,
		):
			try:
				sidebar_doc.standard = 1
				sidebar_doc.save()
			except Exception as e:
				print("Error in setting standard field", e)
