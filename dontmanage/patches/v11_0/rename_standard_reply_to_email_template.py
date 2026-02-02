import dontmanage
from dontmanage.model.rename_doc import rename_doc


def execute():
	if dontmanage.db.table_exists("Standard Reply") and not dontmanage.db.table_exists("Email Template"):
		rename_doc("DocType", "Standard Reply", "Email Template")
		dontmanage.reload_doc("email", "doctype", "email_template")
