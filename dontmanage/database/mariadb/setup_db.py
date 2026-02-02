import os
import sys

import click

import dontmanage
from dontmanage.database.db_manager import DbManager


def get_mariadb_variables():
	return dontmanage._dict(dontmanage.db.sql("show variables"))


def get_mariadb_version(version_string: str = ""):
	# MariaDB classifies their versions as Major (1st and 2nd number), and Minor (3rd number)
	# Example: Version 10.3.13 is Major Version = 10.3, Minor Version = 13
	version_string = version_string or get_mariadb_variables().get("version")
	version = version_string.split("-", 1)[0]
	return version.rsplit(".", 1)


def setup_database(force, verbose, mariadb_user_host_login_scope=None):
	dontmanage.local.session = dontmanage._dict({"user": "Administrator"})

	db_user = dontmanage.conf.db_user
	db_name = dontmanage.local.conf.db_name
	root_conn = get_root_connection()
	dbman = DbManager(root_conn)
	dbman_kwargs = {}

	if mariadb_user_host_login_scope is not None:
		dbman_kwargs["host"] = mariadb_user_host_login_scope

	dbman.create_user(db_user, dontmanage.conf.db_password, **dbman_kwargs)
	if verbose:
		print(f"Created or updated user {db_user}")

	if force or (db_name not in dbman.get_database_list()):
		dbman.drop_database(db_name)
	else:
		print(f"Database {db_name} already exists, please drop it manually or pass `--force`.")
		sys.exit(1)

	dbman.create_database(db_name)
	if verbose:
		print("Created database {}".format(db_name))

	dbman.grant_all_privileges(db_name, db_user, **dbman_kwargs)
	dbman.flush_privileges()
	if verbose:
		print(f"Granted privileges to user {db_user} and database {db_name}")

	# close root connection
	root_conn.close()


def drop_user_and_database(
	db_name,
	db_user,
):
	dontmanage.local.db = get_root_connection()
	dbman = DbManager(dontmanage.local.db)
	dbman.drop_database(db_name)
	dbman.delete_user(db_user, host="%")
	dbman.delete_user(db_user)


def bootstrap_database(verbose, source_sql=None):
	import sys

	dontmanage.connect()
	check_compatible_versions()

	import_db_from_sql(source_sql, verbose)

	dontmanage.connect()
	if "tabDefaultValue" not in dontmanage.db.get_tables(cached=False):
		from click import secho

		secho(
			"Table 'tabDefaultValue' missing in the restored site. "
			"This happens when the backup fails to restore. Please check that the file is valid\n"
			"Do go through the above output to check the exact error message from MariaDB",
			fg="red",
		)
		sys.exit(1)


def import_db_from_sql(source_sql=None, verbose=False):
	if verbose:
		print("Starting database import...")
	db_name = dontmanage.conf.db_name
	if not source_sql:
		source_sql = os.path.join(os.path.dirname(__file__), "framework_mariadb.sql")
	DbManager(dontmanage.local.db).restore_database(
		verbose, db_name, source_sql, dontmanage.conf.db_user, dontmanage.conf.db_password
	)
	if verbose:
		print("Imported from database {}".format(source_sql))


def check_compatible_versions():
	try:
		version = get_mariadb_version()
		version_tuple = tuple(int(v) for v in version[0].split("."))

		if version_tuple < (10, 6):
			click.secho(
				f"Warning: MariaDB version {version} is older than 10.6 which is not supported by DontManage",
				fg="yellow",
			)
		elif version_tuple > (11, 8):
			click.secho(
				f"Warning: MariaDB version {version} is newer than 11.8 which is not yet tested with DontManage Framework.",
				fg="yellow",
			)
	except Exception:
		click.secho(
			"MariaDB version compatibility checks failed, make sure you're running a supported version.",
			fg="yellow",
		)


def get_root_connection():
	if not dontmanage.local.flags.root_connection:
		from getpass import getpass

		if not dontmanage.flags.root_login:
			dontmanage.flags.root_login = (
				dontmanage.conf.get("mariadb_root_login")
				or dontmanage.conf.get("root_login")
				or (sys.__stdin__.isatty() and input("Enter mysql super user [root]: "))
				or "root"
			)

		if not dontmanage.flags.root_password:
			dontmanage.flags.root_password = (
				dontmanage.conf.get("mariadb_root_password")
				or dontmanage.conf.get("root_password")
				or getpass("MySQL root password: ")
			)

		dontmanage.local.flags.root_connection = dontmanage.database.get_db(
			socket=dontmanage.conf.db_socket,
			host=dontmanage.conf.db_host,
			port=dontmanage.conf.db_port,
			user=dontmanage.flags.root_login,
			password=dontmanage.flags.root_password,
			cur_db_name=None,
		)

	return dontmanage.local.flags.root_connection
