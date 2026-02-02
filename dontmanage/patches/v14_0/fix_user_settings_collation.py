import dontmanage


def execute():
	if dontmanage.db.db_type == "mariadb":
		dontmanage.db.sql(
			"ALTER TABLE __UserSettings CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
		)
