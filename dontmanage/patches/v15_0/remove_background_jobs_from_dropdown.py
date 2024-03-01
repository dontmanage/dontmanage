import dontmanage


def execute():
	item = dontmanage.db.exists("Navbar Item", {"item_label": "Background Jobs"})
	if not item:
		return

	dontmanage.delete_doc("Navbar Item", item)
