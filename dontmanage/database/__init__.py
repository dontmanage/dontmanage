# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

# Database Module
# --------------------
from pathlib import Path
from shutil import which

from dontmanage.database.database import savepoint


def setup_database(force, verbose=None, mariadb_user_host_login_scope=None):
	import dontmanage

	if dontmanage.conf.db_type == "mariadb":
		import dontmanage.database.mariadb.setup_db

		return dontmanage.database.mariadb.setup_db.setup_database(force, verbose, mariadb_user_host_login_scope)
	elif dontmanage.conf.db_type == "sqlite":
		import dontmanage.database.sqlite.setup_db

		return dontmanage.database.sqlite.setup_db.setup_database(force, verbose)
	else:
		import dontmanage.database.postgres.setup_db

		return dontmanage.database.postgres.setup_db.setup_database()


def bootstrap_database(verbose=None, source_sql=None):
	import dontmanage

	if dontmanage.conf.db_type == "mariadb":
		import dontmanage.database.mariadb.setup_db

		return dontmanage.database.mariadb.setup_db.bootstrap_database(verbose, source_sql)
	elif dontmanage.conf.db_type == "sqlite":
		import dontmanage.database.sqlite.setup_db

		return dontmanage.database.sqlite.setup_db.bootstrap_database(verbose, source_sql)
	else:
		import dontmanage.database.postgres.setup_db

		return dontmanage.database.postgres.setup_db.bootstrap_database(verbose, source_sql)


def drop_user_and_database(db_name, db_user):
	import dontmanage

	if dontmanage.conf.db_type == "mariadb":
		import dontmanage.database.mariadb.setup_db

		return dontmanage.database.mariadb.setup_db.drop_user_and_database(db_name, db_user)
	elif dontmanage.conf.db_type == "sqlite":
		import dontmanage.database.sqlite.setup_db

		return dontmanage.database.sqlite.setup_db.drop_database(db_name)
	else:
		import dontmanage.database.postgres.setup_db

		return dontmanage.database.postgres.setup_db.drop_user_and_database(db_name, db_user)


def get_db(socket=None, host=None, user=None, password=None, port=None, cur_db_name=None):
	import dontmanage

	conf = dontmanage.local.conf

	if conf.db_type == "postgres":
		import dontmanage.database.postgres.database

		return dontmanage.database.postgres.database.PostgresDatabase(
			socket, host, user, password, port, cur_db_name
		)
	elif conf.db_type == "sqlite":
		import dontmanage.database.sqlite.database

		return dontmanage.database.sqlite.database.SQLiteDatabase(cur_db_name=cur_db_name)
	elif conf.get("use_mysqlclient", 1):
		import dontmanage.database.mariadb.mysqlclient

		return dontmanage.database.mariadb.mysqlclient.MariaDBDatabase(
			socket, host, user, password, port, cur_db_name
		)
	else:
		import dontmanage.database.mariadb.database

		return dontmanage.database.mariadb.database.MariaDBDatabase(
			socket, host, user, password, port, cur_db_name
		)


def get_command(
	socket=None, host=None, port=None, user=None, password=None, db_name=None, extra=None, dump=False
):
	import dontmanage

	if dontmanage.conf.db_type == "mariadb":
		if dump:
			bin, bin_name = which("mariadb-dump") or which("mysqldump"), "mariadb-dump"
		else:
			bin, bin_name = which("mariadb") or which("mysql"), "mariadb"

		command = [f"--user={user}"]
		if socket:
			command.append(f"--socket={socket}")
		elif host and port:
			command.append(f"--host={host}")
			command.append(f"--port={port}")

		if password:
			command.append(f"--password={password}")

		if dump:
			command.extend(
				[
					"--single-transaction",
					"--quick",
					"--lock-tables=false",
				]
			)
		else:
			command.extend(
				[
					"--pager=less -SFX",
					"--safe-updates",
					"--no-auto-rehash",
				]
			)

		command.append(db_name)

		if extra:
			command.extend(extra)

	elif dontmanage.conf.db_type == "sqlite":
		bin, bin_name = which("sqlite3"), "sqlite3"
		db_path = Path(dontmanage.get_site_path()) / "db" / f"{db_name}.db"
		command = [db_path.as_posix()]
		if dump:
			command.append(".dump")

	else:
		if dump:
			bin, bin_name = which("pg_dump"), "pg_dump"
		else:
			bin, bin_name = which("psql"), "psql"

		if socket and password:
			conn_string = f"postgresql://{user}:{password}@/{db_name}?host={socket}"
		elif socket:
			conn_string = f"postgresql://{user}@/{db_name}?host={socket}"
		elif password:
			conn_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
		else:
			conn_string = f"postgresql://{user}@{host}:{port}/{db_name}"

		command = [conn_string]

		if extra:
			command.extend(extra)

	return bin, command, bin_name
