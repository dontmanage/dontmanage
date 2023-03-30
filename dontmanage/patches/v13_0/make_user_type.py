import dontmanage
from dontmanage.utils.install import create_user_type


def execute():
	dontmanage.reload_doc("core", "doctype", "role")
	dontmanage.reload_doc("core", "doctype", "user_document_type")
	dontmanage.reload_doc("core", "doctype", "user_type_module")
	dontmanage.reload_doc("core", "doctype", "user_select_document_type")
	dontmanage.reload_doc("core", "doctype", "user_type")

	create_user_type()
