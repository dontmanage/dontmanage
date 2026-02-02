import dontmanage


def execute():
	for name in ("desktop", "space"):
		dontmanage.delete_doc("Page", name)
