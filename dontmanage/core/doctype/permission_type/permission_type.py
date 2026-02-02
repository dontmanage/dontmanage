# Copyright (c) 2025, DontManage Technologies and contributors
# For license information, please see license.txt

from collections import defaultdict

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document
from dontmanage.modules.export_file import delete_folder
from dontmanage.utils.caching import site_cache

# doctypes where custom fields for permission types will be created
CUSTOM_FIELD_TARGET = ["Custom DocPerm", "DocPerm", "DocShare"]


class PermissionType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		doc_type: DF.Link
		perm_type: DF.Data
	# end: auto-generated types

	def autoname(self):
		self.name = f"{dontmanage.scrub(self.doc_type)}_{dontmanage.scrub(self.perm_type)}"

	def before_insert(self):
		self.perm_type = dontmanage.scrub(self.perm_type)

	def validate(self):
		from dontmanage.permissions import std_rights

		if self.perm_type in std_rights:
			dontmanage.throw(
				_("Permission Type '{0}' is reserved. Please choose another name.").format(self.perm_type)
			)

	def can_write(self):
		return (
			dontmanage.conf.developer_mode
			or dontmanage.flags.in_migrate
			or dontmanage.flags.in_install
			or dontmanage.flags.in_test
		)

	def should_export(self):
		return (
			dontmanage.conf.developer_mode
			and not dontmanage.flags.in_migrate
			and not dontmanage.flags.in_install
			and not dontmanage.flags.in_test
		)

	def get_folder_path(self):
		app = dontmanage.get_doctype_app(self.doc_type)
		folder = dontmanage.get_app_source_path(app, app, "permission_types")
		return folder

	def on_update(self):
		if not self.can_write():
			dontmanage.throw(_("Creation of this document is only permitted in developer mode."))

		for target in CUSTOM_FIELD_TARGET:
			self.create_custom_field(target)

		if self.should_export():
			from dontmanage.modules.export_file import export_to_files

			module = dontmanage.db.get_value("DocType", self.doc_type, "module")
			export_to_files(record_list=[["Permission Type", self.name]], record_module=module)

	def before_export(self, export_doc):
		del export_doc["idx"]
		del export_doc["docstatus"]
		for key in list(export_doc.keys()):
			if key.startswith("_"):
				del export_doc[key]

	def create_custom_field(self, target):
		from dontmanage.custom.doctype.custom_field.custom_field import create_custom_field

		if not self.custom_field_exists(target):
			field = "share_doctype" if target == "DocShare" else "parent"
			depends_on = f"eval:doc.{field} == '{self.doc_type}'"

			create_custom_field(
				target,
				{
					"fieldname": self.perm_type,
					"label": dontmanage.unscrub(self.perm_type),
					"fieldtype": "Check",
					"insert_after": "append",
					"depends_on": depends_on,
				},
			)

	def on_trash(self):
		if not self.can_write():
			dontmanage.throw(_("Deletion of this document is only permitted in developer mode."))

		for target in CUSTOM_FIELD_TARGET:
			self.delete_custom_field(target)

		if self.should_export():
			module = dontmanage.db.get_value("DocType", self.doc_type, "module")
			delete_folder(module, "Permission Type", self.name)

	def delete_custom_field(self, target):
		if name := self.custom_field_exists(target):
			dontmanage.delete_doc("Custom Field", name)

	def custom_field_exists(self, target):
		return dontmanage.db.exists(
			"Custom Field",
			{
				"fieldname": self.perm_type,
				"dt": target,
			},
		)


@site_cache
def get_doctype_ptype_map():
	ptypes = dontmanage.get_all("Permission Type", fields=["perm_type", "doc_type"], order_by="perm_type")

	doctype_ptype_map = defaultdict(list)
	for pt in ptypes:
		if pt.perm_type not in doctype_ptype_map[pt.doc_type]:
			doctype_ptype_map[pt.doc_type].append(pt.perm_type)
	return dict(doctype_ptype_map)
