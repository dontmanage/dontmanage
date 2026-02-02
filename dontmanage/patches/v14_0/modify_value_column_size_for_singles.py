import dontmanage


def execute():
	if dontmanage.db.db_type == "mariadb":
		dontmanage.db.sql_ddl("alter table `tabSingles` modify column `value` longtext")
