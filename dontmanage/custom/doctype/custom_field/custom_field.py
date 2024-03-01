# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage import _
from dontmanage.model import core_doctypes_list
from dontmanage.model.docfield import supports_translation
from dontmanage.model.document import Document
from dontmanage.query_builder.functions import IfNull
from dontmanage.utils import cstr, random_string


class CustomField(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		allow_in_quick_entry: DF.Check
		allow_on_submit: DF.Check
		bold: DF.Check
		collapsible: DF.Check
		collapsible_depends_on: DF.Code | None
		columns: DF.Int
		default: DF.Text | None
		depends_on: DF.Code | None
		description: DF.Text | None
		dt: DF.Link
		fetch_from: DF.SmallText | None
		fetch_if_empty: DF.Check
		fieldname: DF.Data | None
		fieldtype: DF.Literal[
			"Autocomplete",
			"Attach",
			"Attach Image",
			"Barcode",
			"Button",
			"Check",
			"Code",
			"Color",
			"Column Break",
			"Currency",
			"Data",
			"Date",
			"Datetime",
			"Duration",
			"Dynamic Link",
			"Float",
			"Fold",
			"Geolocation",
			"Heading",
			"HTML",
			"HTML Editor",
			"Icon",
			"Image",
			"Int",
			"JSON",
			"Link",
			"Long Text",
			"Markdown Editor",
			"Password",
			"Percent",
			"Phone",
			"Read Only",
			"Rating",
			"Section Break",
			"Select",
			"Signature",
			"Small Text",
			"Tab Break",
			"Table",
			"Table MultiSelect",
			"Text",
			"Text Editor",
			"Time",
		]
		hidden: DF.Check
		hide_border: DF.Check
		hide_days: DF.Check
		hide_seconds: DF.Check
		ignore_user_permissions: DF.Check
		ignore_xss_filter: DF.Check
		in_global_search: DF.Check
		in_list_view: DF.Check
		in_preview: DF.Check
		in_standard_filter: DF.Check
		insert_after: DF.Literal
		is_system_generated: DF.Check
		is_virtual: DF.Check
		label: DF.Data | None
		length: DF.Int
		mandatory_depends_on: DF.Code | None
		module: DF.Link | None
		no_copy: DF.Check
		non_negative: DF.Check
		options: DF.SmallText | None
		permlevel: DF.Int
		precision: DF.Literal["", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
		print_hide: DF.Check
		print_hide_if_no_value: DF.Check
		print_width: DF.Data | None
		read_only: DF.Check
		read_only_depends_on: DF.Code | None
		report_hide: DF.Check
		reqd: DF.Check
		search_index: DF.Check
		show_dashboard: DF.Check
		sort_options: DF.Check
		translatable: DF.Check
		unique: DF.Check
		width: DF.Data | None

	# end: auto-generated types
	def autoname(self):
		self.set_fieldname()
		self.name = self.dt + "-" + self.fieldname

	def set_fieldname(self):
		restricted = (
			"name",
			"parent",
			"creation",
			"modified",
			"modified_by",
			"parentfield",
			"parenttype",
			"file_list",
			"flags",
			"docstatus",
		)
		if not self.fieldname:
			label = self.label
			if not label:
				if self.fieldtype in ["Section Break", "Column Break", "Tab Break"]:
					label = self.fieldtype + "_" + str(random_string(5))
				else:
					dontmanage.throw(_("Label is mandatory"))

			# remove special characters from fieldname
			self.fieldname = "".join(
				[c for c in cstr(label).replace(" ", "_") if c.isdigit() or c.isalpha() or c == "_"]
			)
			self.fieldname = f"custom_{self.fieldname}"

		# fieldnames should be lowercase
		self.fieldname = self.fieldname.lower()

		if self.fieldname in restricted:
			self.fieldname = self.fieldname + "1"

	def before_insert(self):
		self.set_fieldname()

	def validate(self):
		# these imports have been added to avoid cyclical import, should fix in future
		from dontmanage.core.doctype.doctype.doctype import check_fieldname_conflicts
		from dontmanage.custom.doctype.customize_form.customize_form import CustomizeForm

		# don't always get meta to improve performance
		# setting idx is just an improvement, not a requirement
		if self.is_new() or self.insert_after == "append":
			meta = dontmanage.get_meta(self.dt, cached=False)
			fieldnames = [df.fieldname for df in meta.get("fields")]

			if self.is_new() and self.fieldname in fieldnames:
				dontmanage.throw(
					_("A field with the name {0} already exists in {1}").format(
						dontmanage.bold(self.fieldname), self.dt
					)
				)

			if self.insert_after == "append":
				self.insert_after = fieldnames[-1]

			if self.insert_after and self.insert_after in fieldnames:
				self.idx = fieldnames.index(self.insert_after) + 1

		if (
			not self.is_virtual
			and (doc_before_save := self.get_doc_before_save())
			and (old_fieldtype := doc_before_save.fieldtype) != self.fieldtype
			and not CustomizeForm.allow_fieldtype_change(old_fieldtype, self.fieldtype)
		):
			dontmanage.throw(
				_("Fieldtype cannot be changed from {0} to {1}").format(old_fieldtype, self.fieldtype)
			)

		if not self.fieldname:
			dontmanage.throw(_("Fieldname not set for Custom Field"))

		if self.get("translatable", 0) and not supports_translation(self.fieldtype):
			self.translatable = 0

		check_fieldname_conflicts(self)

	def on_update(self):
		# validate field
		if not self.flags.ignore_validate:
			from dontmanage.core.doctype.doctype.doctype import validate_fields_for_doctype

			validate_fields_for_doctype(self.dt)

		# clear cache and update the schema
		if not dontmanage.flags.in_create_custom_fields:
			dontmanage.clear_cache(doctype=self.dt)
			dontmanage.db.updatedb(self.dt)

	def on_trash(self):
		# check if Admin owned field
		if self.owner == "Administrator" and dontmanage.session.user != "Administrator":
			dontmanage.throw(
				_(
					"Custom Field {0} is created by the Administrator and can only be deleted through the Administrator account."
				).format(dontmanage.bold(self.label))
			)

		# delete property setter entries
		dontmanage.db.delete("Property Setter", {"doc_type": self.dt, "field_name": self.fieldname})

		# update doctype layouts
		doctype_layouts = dontmanage.get_all("DocType Layout", filters={"document_type": self.dt}, pluck="name")

		for layout in doctype_layouts:
			layout_doc = dontmanage.get_doc("DocType Layout", layout)
			for field in layout_doc.fields:
				if field.fieldname == self.fieldname:
					layout_doc.remove(field)
					layout_doc.save()
					break

		dontmanage.clear_cache(doctype=self.dt)

	def validate_insert_after(self, meta):
		if not meta.get_field(self.insert_after):
			dontmanage.throw(
				_(
					"Insert After field '{0}' mentioned in Custom Field '{1}', with label '{2}', does not exist"
				).format(self.insert_after, self.name, self.label),
				dontmanage.DoesNotExistError,
			)

		if self.fieldname == self.insert_after:
			dontmanage.throw(_("Insert After cannot be set as {0}").format(meta.get_label(self.insert_after)))


@dontmanage.whitelist()
def get_fields_label(doctype=None):
	meta = dontmanage.get_meta(doctype)

	if doctype in core_doctypes_list:
		return dontmanage.msgprint(_("Custom Fields cannot be added to core DocTypes."))

	if meta.custom:
		return dontmanage.msgprint(_("Custom Fields can only be added to a standard DocType."))

	return [
		{"value": df.fieldname or "", "label": _(df.label, context=df.parent) if df.label else ""}
		for df in dontmanage.get_meta(doctype).get("fields")
	]


def create_custom_field_if_values_exist(doctype, df):
	df = dontmanage._dict(df)
	if df.fieldname in dontmanage.db.get_table_columns(doctype) and dontmanage.db.count(
		dt=doctype, filters=IfNull(df.fieldname, "") != ""
	):
		create_custom_field(doctype, df)


def create_custom_field(doctype, df, ignore_validate=False, is_system_generated=True):
	df = dontmanage._dict(df)
	if not df.fieldname and df.label:
		df.fieldname = dontmanage.scrub(df.label)
	if not dontmanage.db.get_value("Custom Field", {"dt": doctype, "fieldname": df.fieldname}):
		custom_field = dontmanage.get_doc(
			{
				"doctype": "Custom Field",
				"dt": doctype,
				"permlevel": 0,
				"fieldtype": "Data",
				"hidden": 0,
				"is_system_generated": is_system_generated,
			}
		)
		custom_field.update(df)
		custom_field.flags.ignore_validate = ignore_validate
		custom_field.insert()
		return custom_field


def create_custom_fields(custom_fields: dict, ignore_validate=False, update=True):
	"""Add / update multiple custom fields

	:param custom_fields: example `{'Sales Invoice': [dict(fieldname='test')]}`"""

	try:
		dontmanage.flags.in_create_custom_fields = True
		doctypes_to_update = set()

		if dontmanage.flags.in_setup_wizard:
			ignore_validate = True

		for doctypes, fields in custom_fields.items():
			if isinstance(fields, dict):
				# only one field
				fields = [fields]

			if isinstance(doctypes, str):
				# only one doctype
				doctypes = (doctypes,)

			for doctype in doctypes:
				doctypes_to_update.add(doctype)

				for df in fields:
					field = dontmanage.db.get_value("Custom Field", {"dt": doctype, "fieldname": df["fieldname"]})
					if not field:
						try:
							df = df.copy()
							df["owner"] = "Administrator"
							create_custom_field(doctype, df, ignore_validate=ignore_validate)

						except dontmanage.exceptions.DuplicateEntryError:
							pass

					elif update:
						custom_field = dontmanage.get_doc("Custom Field", field)
						custom_field.flags.ignore_validate = ignore_validate
						custom_field.update(df)
						custom_field.save()

		for doctype in doctypes_to_update:
			dontmanage.clear_cache(doctype=doctype)
			dontmanage.db.updatedb(doctype)

	finally:
		dontmanage.flags.in_create_custom_fields = False


@dontmanage.whitelist()
def rename_fieldname(custom_field: str, fieldname: str):
	dontmanage.only_for("System Manager")

	field: CustomField = dontmanage.get_doc("Custom Field", custom_field)
	parent_doctype = field.dt
	old_fieldname = field.fieldname
	field.fieldname = fieldname
	field.set_fieldname()
	new_fieldname = field.fieldname

	if field.is_system_generated:
		dontmanage.throw(_("System Generated Fields can not be renamed"))
	if dontmanage.db.has_column(parent_doctype, fieldname):
		dontmanage.throw(_("Can not rename as column {0} is already present on DocType.").format(fieldname))
	if old_fieldname == new_fieldname:
		dontmanage.msgprint(_("Old and new fieldnames are same."), alert=True)
		return

	if dontmanage.db.has_column(field.dt, old_fieldname):
		dontmanage.db.rename_column(parent_doctype, old_fieldname, new_fieldname)

	# Update in DB after alter column is successful, alter column will implicitly commit, so it's
	# best to commit change on field too to avoid any possible mismatch between two.
	field.db_set("fieldname", field.fieldname, notify=True)
	_update_fieldname_references(field, old_fieldname, new_fieldname)

	dontmanage.db.commit()
	dontmanage.clear_cache()


def _update_fieldname_references(field: CustomField, old_fieldname: str, new_fieldname: str) -> None:
	# Passwords are stored in auth table, so column name needs to be updated there.
	if field.fieldtype == "Password":
		Auth = dontmanage.qb.Table("__Auth")
		dontmanage.qb.update(Auth).set(Auth.fieldname, new_fieldname).where(
			(Auth.doctype == field.dt) & (Auth.fieldname == old_fieldname)
		).run()

	# Update ordering reference.
	dontmanage.db.set_value(
		"Custom Field",
		{"insert_after": old_fieldname, "dt": field.dt},
		"insert_after",
		new_fieldname,
	)
