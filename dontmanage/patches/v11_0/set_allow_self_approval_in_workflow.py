import dontmanage


def execute():
	dontmanage.reload_doc("workflow", "doctype", "workflow_transition")
	dontmanage.db.sql("update `tabWorkflow Transition` set allow_self_approval=1")
