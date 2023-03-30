import dontmanage
from dontmanage.model.rename_doc import rename_doc


def execute():
	if dontmanage.db.table_exists("Workflow Action") and not dontmanage.db.table_exists(
		"Workflow Action Master"
	):
		rename_doc("DocType", "Workflow Action", "Workflow Action Master")
		dontmanage.reload_doc("workflow", "doctype", "workflow_action_master")
