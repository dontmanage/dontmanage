import dontmanage


def execute():
	"""
	Rename the Marketing Campaign table to UTM Campaign table
	"""
	if dontmanage.db.exists("DocType", "UTM Campaign"):
		return

	if not dontmanage.db.exists("DocType", "Marketing Campaign"):
		return

	dontmanage.rename_doc("DocType", "Marketing Campaign", "UTM Campaign", force=True)
	dontmanage.reload_doctype("UTM Campaign", force=True)
