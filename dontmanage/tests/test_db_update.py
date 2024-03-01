import dontmanage
from dontmanage.core.doctype.doctype.test_doctype import new_doctype
from dontmanage.core.utils import find
from dontmanage.custom.doctype.property_setter.property_setter import make_property_setter
from dontmanage.query_builder.utils import db_type_is
from dontmanage.tests.test_query_builder import run_only_if
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import cstr


class TestDBUpdate(DontManageTestCase):
	def test_db_update(self):
		doctype = "User"
		dontmanage.reload_doctype("User", force=True)
		dontmanage.model.meta.trim_tables("User")
		make_property_setter(doctype, "bio", "fieldtype", "Text", "Data")
		make_property_setter(doctype, "middle_name", "fieldtype", "Data", "Text")
		make_property_setter(doctype, "enabled", "default", "1", "Int")

		dontmanage.db.updatedb(doctype)

		field_defs = get_field_defs(doctype)
		table_columns = dontmanage.db.get_table_columns_description(f"tab{doctype}")

		self.assertEqual(len(field_defs), len(table_columns))

		for field_def in field_defs:
			fieldname = field_def.get("fieldname")
			table_column = find(table_columns, lambda d: d.get("name") == fieldname)

			fieldtype = get_fieldtype_from_def(field_def)

			fallback_default = (
				"0" if field_def.get("fieldtype") in dontmanage.model.numeric_fieldtypes else "NULL"
			)
			default = field_def.default if field_def.default is not None else fallback_default

			self.assertEqual(fieldtype, table_column.type)
			self.assertIn(cstr(table_column.default) or "NULL", [cstr(default), f"'{default}'"])

	def test_index_and_unique_constraints(self):
		doctype = "User"
		dontmanage.reload_doctype("User", force=True)
		dontmanage.model.meta.trim_tables("User")

		make_property_setter(doctype, "middle_name", "unique", "1", "Check")
		dontmanage.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "unique", "0", "Check")
		dontmanage.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertFalse(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "search_index", "1", "Check")
		dontmanage.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.index)

		make_property_setter(doctype, "middle_name", "search_index", "0", "Check")
		dontmanage.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertFalse(middle_name_in_table.index)

		make_property_setter(doctype, "middle_name", "search_index", "1", "Check")
		make_property_setter(doctype, "middle_name", "unique", "1", "Check")
		dontmanage.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.index)
		self.assertTrue(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "search_index", "1", "Check")
		make_property_setter(doctype, "middle_name", "unique", "0", "Check")
		dontmanage.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertTrue(middle_name_in_table.index)
		self.assertFalse(middle_name_in_table.unique)

		make_property_setter(doctype, "middle_name", "search_index", "0", "Check")
		make_property_setter(doctype, "middle_name", "unique", "1", "Check")
		dontmanage.db.updatedb(doctype)
		middle_name_in_table = get_table_column("User", "middle_name")
		self.assertFalse(middle_name_in_table.index)
		self.assertTrue(middle_name_in_table.unique)

		# explicitly make a text index
		dontmanage.db.add_index(doctype, ["email_signature(200)"])
		dontmanage.db.updatedb(doctype)
		email_sig_column = get_table_column("User", "email_signature")
		self.assertEqual(email_sig_column.index, 1)

	def check_unique_indexes(self, doctype: str, field: str):
		indexes = dontmanage.db.sql(
			f"""show index from `tab{doctype}` where column_name = '{field}' and Non_unique = 0""",
			as_dict=1,
		)
		self.assertEqual(
			len(indexes), 1, msg=f"There should be 1 index on {doctype}.{field}, found {indexes}"
		)

	@run_only_if(db_type_is.MARIADB)
	def test_unique_index_on_install(self):
		"""Only one unique index should be added"""
		for dt in dontmanage.get_all("DocType", {"is_virtual": 0, "issingle": 0}, pluck="name"):
			doctype = dontmanage.get_meta(dt)
			fields = doctype.get("fields", filters={"unique": 1})
			for field in fields:
				with self.subTest(f"Checking index {doctype.name} - {field.fieldname}"):
					self.check_unique_indexes(doctype.name, field.fieldname)

	@run_only_if(db_type_is.MARIADB)
	def test_unique_index_on_alter(self):
		"""Only one unique index should be added"""

		doctype = new_doctype(unique=1).insert()
		field = "some_fieldname"

		self.check_unique_indexes(doctype.name, field)
		doctype.fields[0].length = 142
		doctype.save()
		self.check_unique_indexes(doctype.name, field)

		doctype.fields[0].unique = 0
		doctype.save()

		doctype.fields[0].unique = 1
		doctype.save()
		self.check_unique_indexes(doctype.name, field)

		# New column with a unique index
		# This works because index name is same as fieldname.
		new_field = dontmanage.copy_doc(doctype.fields[0])
		new_field.fieldname = "duplicate_field"
		doctype.append("fields", new_field)
		doctype.save()
		self.check_unique_indexes(doctype.name, new_field.fieldname)

		doctype.delete()
		dontmanage.db.commit()


def get_fieldtype_from_def(field_def):
	fieldtuple = dontmanage.db.type_map.get(field_def.fieldtype, ("", 0))
	fieldtype = fieldtuple[0]
	if fieldtype in ("varchar", "datetime", "int"):
		fieldtype += f"({field_def.length or fieldtuple[1]})"
	return fieldtype


def get_field_defs(doctype):
	meta = dontmanage.get_meta(doctype, cached=False)
	field_defs = meta.get_fieldnames_with_value(True)
	field_defs += get_other_fields_meta(meta)
	return field_defs


def get_other_fields_meta(meta):
	default_fields_map = {
		"name": ("Data", 0),
		"owner": ("Data", 0),
		"modified_by": ("Data", 0),
		"creation": ("Datetime", 0),
		"modified": ("Datetime", 0),
		"idx": ("Int", 8),
		"docstatus": ("Check", 0),
	}

	optional_fields = dontmanage.db.OPTIONAL_COLUMNS
	if meta.track_seen:
		optional_fields.append("_seen")

	child_table_fields_map = {}
	if meta.istable:
		child_table_fields_map.update({field: ("Data", 0) for field in dontmanage.db.CHILD_TABLE_COLUMNS})

	optional_fields_map = {field: ("Text", 0) for field in optional_fields}
	fields = dict(default_fields_map, **optional_fields_map, **child_table_fields_map)
	return [
		dontmanage._dict({"fieldname": field, "fieldtype": _type, "length": _length})
		for field, (_type, _length) in fields.items()
	]


def get_table_column(doctype, fieldname):
	table_columns = dontmanage.db.get_table_columns_description(f"tab{doctype}")
	return find(table_columns, lambda d: d.get("name") == fieldname)
