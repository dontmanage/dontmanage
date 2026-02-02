import dontmanage
from dontmanage.desk.page.setup_wizard.install_fixtures import update_global_search_doctypes


def execute():
	dontmanage.reload_doc("desk", "doctype", "global_search_doctype")
	dontmanage.reload_doc("desk", "doctype", "global_search_settings")
	update_global_search_doctypes()
