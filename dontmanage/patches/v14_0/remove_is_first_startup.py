import dontmanage


def execute():
	singles = dontmanage.qb.Table("tabSingles")
	dontmanage.qb.from_(singles).delete().where(
		(singles.doctype == "System Settings") & (singles.field == "is_first_startup")
	).run()
