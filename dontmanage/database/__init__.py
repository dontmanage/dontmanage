# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

# Database Module
# --------------------

from dontmanage.database.database import savepoint


def setup_database(force, source_sql=None, verbose=None, no_mariadb_socket=False):
	import dontmanage

	if dontmanage.conf.db_type == "postgres":
		import dontmanage.database.postgres.setup_db

		return dontmanage.database.postgres.setup_db.setup_database(force, source_sql, verbose)
	else:
		import dontmanage.database.mariadb.setup_db

		return dontmanage.database.mariadb.setup_db.setup_database(
			force, source_sql, verbose, no_mariadb_socket=no_mariadb_socket
		)


def drop_user_and_database(db_name, root_login=None, root_password=None):
	import dontmanage

	if dontmanage.conf.db_type == "postgres":
		import dontmanage.database.postgres.setup_db

		return dontmanage.database.postgres.setup_db.drop_user_and_database(
			db_name, root_login, root_password
		)
	else:
		import dontmanage.database.mariadb.setup_db

		return dontmanage.database.mariadb.setup_db.drop_user_and_database(
			db_name, root_login, root_password
		)


def get_db(host=None, user=None, password=None, port=None):
	import dontmanage

	if dontmanage.conf.db_type == "postgres":
		import dontmanage.database.postgres.database

		return dontmanage.database.postgres.database.PostgresDatabase(host, user, password, port=port)
	else:
		import dontmanage.database.mariadb.database

		return dontmanage.database.mariadb.database.MariaDBDatabase(host, user, password, port=port)


def setup_help_database(help_db_name):
	import dontmanage

	if dontmanage.conf.db_type == "postgres":
		import dontmanage.database.postgres.setup_db

		return dontmanage.database.postgres.setup_db.setup_help_database(help_db_name)
	else:
		import dontmanage.database.mariadb.setup_db

		return dontmanage.database.mariadb.setup_db.setup_help_database(help_db_name)
