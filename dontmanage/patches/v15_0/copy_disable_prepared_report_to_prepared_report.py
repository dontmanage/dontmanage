import dontmanage


def execute():
	table = dontmanage.qb.DocType("Report")
	dontmanage.qb.update(table).set(table.prepared_report, 0).where(table.disable_prepared_report == 1)
