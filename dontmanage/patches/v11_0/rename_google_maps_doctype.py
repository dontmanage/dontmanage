import dontmanage
from dontmanage.model.rename_doc import rename_doc


def execute():
	if dontmanage.db.exists("DocType", "Google Maps") and not dontmanage.db.exists(
		"DocType", "Google Maps Settings"
	):
		rename_doc("DocType", "Google Maps", "Google Maps Settings")
