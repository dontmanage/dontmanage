import dontmanage


def execute():
	dontmanage.reload_doctype("Letter Head")

	# source of all existing letter heads must be HTML
	dontmanage.db.sql("update `tabLetter Head` set source = 'HTML'")
