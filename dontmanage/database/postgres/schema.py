import dontmanage
from dontmanage import _
from dontmanage.database.schema import DBTable, get_definition
from dontmanage.model import log_types
from dontmanage.utils import cint, flt


class PostgresTable(DBTable):
	def create(self):
		varchar_len = dontmanage.db.VARCHAR_LEN
		name_column = f"name varchar({varchar_len}) primary key"

		additional_definitions = ""
		# columns
		column_defs = self.get_column_definitions()
		if column_defs:
			additional_definitions += ",\n".join(column_defs)

		# child table columns
		if self.meta.get("istable") or 0:
			if column_defs:
				additional_definitions += ",\n"

			additional_definitions += ",\n".join(
				(
					f"parent varchar({varchar_len})",
					f"parentfield varchar({varchar_len})",
					f"parenttype varchar({varchar_len})",
				)
			)

		# creating sequence(s)
		if (
			not self.meta.issingle and self.meta.autoname == "autoincrement"
		) or self.doctype in log_types:

			dontmanage.db.create_sequence(self.doctype, check_not_exists=True, cache=dontmanage.db.SEQUENCE_CACHE)
			name_column = "name bigint primary key"

		# TODO: set docstatus length
		# create table
		dontmanage.db.sql(
			f"""create table `{self.table_name}` (
			{name_column},
			creation timestamp(6),
			modified timestamp(6),
			modified_by varchar({varchar_len}),
			owner varchar({varchar_len}),
			docstatus smallint not null default '0',
			idx bigint not null default '0',
			{additional_definitions}
			)"""
		)

		self.create_indexes()
		dontmanage.db.commit()

	def create_indexes(self):
		create_index_query = ""
		for key, col in self.columns.items():
			if (
				col.set_index
				and col.fieldtype in dontmanage.db.type_map
				and dontmanage.db.type_map.get(col.fieldtype)[0] not in ("text", "longtext")
			):
				create_index_query += (
					'CREATE INDEX IF NOT EXISTS "{index_name}" ON `{table_name}`(`{field}`);'.format(
						index_name=col.fieldname, table_name=self.table_name, field=col.fieldname
					)
				)
		if create_index_query:
			# nosemgrep
			dontmanage.db.sql(create_index_query)

	def alter(self):
		for col in self.columns.values():
			col.build_for_alter_table(self.current_columns.get(col.fieldname.lower()))

		query = []

		for col in self.add_column:
			query.append(f"ADD COLUMN `{col.fieldname}` {col.get_definition()}")

		for col in self.change_type:
			using_clause = ""
			if col.fieldtype in ("Datetime"):
				# The USING option of SET DATA TYPE can actually specify any expression
				# involving the old values of the row
				# read more https://www.postgresql.org/docs/9.1/sql-altertable.html
				using_clause = f"USING {col.fieldname}::timestamp without time zone"
			elif col.fieldtype in ("Check"):
				using_clause = f"USING {col.fieldname}::smallint"

			query.append(
				"ALTER COLUMN `{}` TYPE {} {}".format(
					col.fieldname,
					get_definition(col.fieldtype, precision=col.precision, length=col.length),
					using_clause,
				)
			)

		for col in self.set_default:
			if col.fieldname == "name":
				continue

			if col.fieldtype in ("Check", "Int"):
				col_default = cint(col.default)

			elif col.fieldtype in ("Currency", "Float", "Percent"):
				col_default = flt(col.default)

			elif not col.default:
				col_default = "NULL"

			else:
				col_default = f"{dontmanage.db.escape(col.default)}"

			query.append(f"ALTER COLUMN `{col.fieldname}` SET DEFAULT {col_default}")

		create_contraint_query = ""
		for col in self.add_index:
			# if index key not exists
			create_contraint_query += (
				'CREATE INDEX IF NOT EXISTS "{index_name}" ON `{table_name}`(`{field}`);'.format(
					index_name=col.fieldname, table_name=self.table_name, field=col.fieldname
				)
			)

		for col in self.add_unique:
			# if index key not exists
			create_contraint_query += (
				'CREATE UNIQUE INDEX IF NOT EXISTS "unique_{index_name}" ON `{table_name}`(`{field}`);'.format(
					index_name=col.fieldname, table_name=self.table_name, field=col.fieldname
				)
			)

		drop_contraint_query = ""
		for col in self.drop_index:
			# primary key
			if col.fieldname != "name":
				# if index key exists
				drop_contraint_query += f'DROP INDEX IF EXISTS "{col.fieldname}" ;'

		for col in self.drop_unique:
			# primary key
			if col.fieldname != "name":
				# if index key exists
				drop_contraint_query += f'DROP INDEX IF EXISTS "unique_{col.fieldname}" ;'
		try:
			if query:
				final_alter_query = "ALTER TABLE `{}` {}".format(self.table_name, ", ".join(query))
				# nosemgrep
				dontmanage.db.sql(final_alter_query)
			if create_contraint_query:
				# nosemgrep
				dontmanage.db.sql(create_contraint_query)
			if drop_contraint_query:
				# nosemgrep
				dontmanage.db.sql(drop_contraint_query)
		except Exception as e:
			# sanitize
			if dontmanage.db.is_duplicate_fieldname(e):
				dontmanage.throw(str(e))
			elif dontmanage.db.is_duplicate_entry(e):
				fieldname = str(e).split("'")[-2]
				dontmanage.throw(
					_("{0} field cannot be set as unique in {1}, as there are non-unique existing values").format(
						fieldname, self.table_name
					)
				)
			else:
				raise e
