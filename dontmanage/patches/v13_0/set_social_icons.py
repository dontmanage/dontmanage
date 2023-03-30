import dontmanage


def execute():
	providers = dontmanage.get_all("Social Login Key")

	for provider in providers:
		doc = dontmanage.get_doc("Social Login Key", provider)
		doc.set_icon()
		doc.save()
