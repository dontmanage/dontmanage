import dontmanage


def execute():
	dontmanage.delete_doc_if_exists("DocType", "Web View")
	dontmanage.delete_doc_if_exists("DocType", "Web View Component")
	dontmanage.delete_doc_if_exists("DocType", "CSS Class")
