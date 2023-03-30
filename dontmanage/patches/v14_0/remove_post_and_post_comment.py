import dontmanage


def execute():
	dontmanage.delete_doc_if_exists("DocType", "Post")
	dontmanage.delete_doc_if_exists("DocType", "Post Comment")
