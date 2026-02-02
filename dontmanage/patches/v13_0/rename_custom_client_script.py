import dontmanage
from dontmanage.model.rename_doc import rename_doc


def execute():
	if dontmanage.db.exists("DocType", "Client Script"):
		return

	dontmanage.flags.ignore_route_conflict_validation = True
	rename_doc("DocType", "Custom Script", "Client Script")
	dontmanage.flags.ignore_route_conflict_validation = False

	dontmanage.reload_doctype("Client Script", force=True)
