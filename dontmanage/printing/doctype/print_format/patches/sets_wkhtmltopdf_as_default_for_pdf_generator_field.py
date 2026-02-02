import dontmanage


def execute():
	"""sets "wkhtmltopdf" as default for pdf_generator field"""
	for pf in dontmanage.get_all("Print Format", pluck="name"):
		dontmanage.db.set_value("Print Format", pf, "pdf_generator", "wkhtmltopdf", update_modified=False)
