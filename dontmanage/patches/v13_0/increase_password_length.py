import dontmanage


def execute():
	dontmanage.db.change_column_type("__Auth", column="password", type="TEXT")
