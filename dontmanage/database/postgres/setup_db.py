import os
import re

import dontmanage
from dontmanage.database.db_manager import DbManager
from dontmanage.utils import cint


def setup_database():
	root_conn = get_root_connection()
	root_conn.commit()
	root_conn.sql("end")
	root_conn.sql(f'DROP DATABASE IF EXISTS "{dontmanage.conf.db_name}"')

	# If user exists, just update password
	if root_conn.sql(f"SELECT 1 FROM pg_roles WHERE rolname='{dontmanage.conf.db_user}'"):
		root_conn.sql(f"ALTER USER \"{dontmanage.conf.db_user}\" WITH PASSWORD '{dontmanage.conf.db_password}'")
	else:
		root_conn.sql(f"CREATE USER \"{dontmanage.conf.db_user}\" WITH PASSWORD '{dontmanage.conf.db_password}'")
	root_conn.sql(f'CREATE DATABASE "{dontmanage.conf.db_name}"')
	root_conn.sql(f'GRANT ALL PRIVILEGES ON DATABASE "{dontmanage.conf.db_name}" TO "{dontmanage.conf.db_user}"')
	if psql_version := root_conn.sql("SHOW server_version_num", as_dict=True):
		semver_version_num = psql_version[0].get("server_version_num") or "140000"
		if cint(semver_version_num) > 150000:
			root_conn.sql(f'ALTER DATABASE "{dontmanage.conf.db_name}" OWNER TO "{dontmanage.conf.db_user}"')
	root_conn.close()


def bootstrap_database(verbose, source_sql=None):
	dontmanage.connect()
	import_db_from_sql(source_sql, verbose)

	dontmanage.connect()
	if "tabDefaultValue" not in dontmanage.db.get_tables():
		import sys

		from click import secho

		secho(
			"Table 'tabDefaultValue' missing in the restored site. "
			"This happens when the backup fails to restore. Please check that the file is valid\n"
			"Do go through the above output to check the exact error message from Postgres",
			fg="red",
		)
		sys.exit(1)


def import_db_from_sql(source_sql=None, verbose=False):
	if verbose:
		print("Starting database import...")
	db_name = dontmanage.conf.db_name
	if not source_sql:
		source_sql = os.path.join(os.path.dirname(__file__), "framework_postgres.sql")
	DbManager(dontmanage.local.db).restore_database(
		verbose, db_name, source_sql, dontmanage.conf.db_user, dontmanage.conf.db_password
	)
	if verbose:
		print("Imported from database {}".format(source_sql))


def get_root_connection():
	if not dontmanage.local.flags.root_connection:
		import sys
		from getpass import getpass

		if not dontmanage.flags.root_login:
			dontmanage.flags.root_login = (
				dontmanage.conf.get("postgres_root_login")
				or dontmanage.conf.get("root_login")
				or (sys.__stdin__.isatty() and input("Enter postgres super user [postgres]: "))
				or "postgres"
			)

		if not dontmanage.flags.root_password:
			dontmanage.flags.root_password = (
				dontmanage.conf.get("postgres_root_password")
				or dontmanage.conf.get("root_password")
				or getpass("Postgres super user password: ")
			)

		dontmanage.local.flags.root_connection = dontmanage.database.get_db(
			socket=dontmanage.conf.db_socket,
			host=dontmanage.conf.db_host,
			port=dontmanage.conf.db_port,
			user=dontmanage.flags.root_login,
			password=dontmanage.flags.root_password,
			cur_db_name=dontmanage.flags.root_login,
		)

	return dontmanage.local.flags.root_connection


def drop_user_and_database(db_name, db_user):
	root_conn = get_root_connection()
	root_conn.commit()
	root_conn.sql(
		"SELECT pg_terminate_backend (pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = %s",
		(db_name,),
	)
	root_conn.sql("end")
	root_conn.sql(f"DROP DATABASE IF EXISTS {db_name}")
	root_conn.sql(f"DROP USER IF EXISTS {db_user}")
