import dontmanage

# This patch deletes all the duplicate indexes created for same column
# The patch only checks for indexes with UNIQUE constraints


def execute():
	if dontmanage.db.db_type != "mariadb":
		return

	all_tables = dontmanage.db.get_tables()
	final_deletion_map = dontmanage._dict()

	for table in all_tables:
		indexes_to_keep_map = dontmanage._dict()
		indexes_to_delete = []
		index_info = dontmanage.db.sql(
			f"""SHOW INDEX FROM `{table}`
				WHERE Seq_in_index = 1
				AND Non_unique=0""",
			as_dict=1,
		)

		for index in index_info:
			if not indexes_to_keep_map.get(index.Column_name):
				indexes_to_keep_map[index.Column_name] = index
			else:
				indexes_to_delete.append(index.Key_name)

		if indexes_to_delete:
			final_deletion_map[table] = indexes_to_delete

	for table_name, index_list in final_deletion_map.items():
		for index in index_list:
			try:
				if is_clustered_index(table_name, index):
					continue
				dontmanage.db.sql_ddl(f"ALTER TABLE `{table_name}` DROP INDEX `{index}`")
			except Exception as e:
				dontmanage.log_error("Failed to drop index")
				print(f"x Failed to drop index {index} from {table_name}\n {str(e)}")
			else:
				print(f"✓ dropped {index} index from {table}")


def is_clustered_index(table, index_name):
	return bool(
		dontmanage.db.sql(
			f"""SHOW INDEX FROM `{table}`
			WHERE Key_name = "{index_name}"
				AND Seq_in_index = 2
			""",
			as_dict=True,
		)
	)
