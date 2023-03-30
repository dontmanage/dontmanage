import dontmanage


def execute():
	if dontmanage.db.table_exists("Prepared Report"):
		dontmanage.reload_doc("core", "doctype", "prepared_report")
		prepared_reports = dontmanage.get_all("Prepared Report")
		for report in prepared_reports:
			dontmanage.delete_doc("Prepared Report", report.name)
