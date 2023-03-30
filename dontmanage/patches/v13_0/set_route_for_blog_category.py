import dontmanage


def execute():
	categories = dontmanage.get_list("Blog Category")
	for category in categories:
		doc = dontmanage.get_doc("Blog Category", category["name"])
		doc.set_route()
		doc.save()
