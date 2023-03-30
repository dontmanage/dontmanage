# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

from typing import TYPE_CHECKING

import dontmanage
from dontmanage.desk.utils import slug
from dontmanage.model.document import Document

if TYPE_CHECKING:
	from dontmanage.core.doctype.docfield.docfield import DocField


class DocTypeLayout(Document):
	def validate(self):
		if not self.route:
			self.route = slug(self.name)

	@dontmanage.whitelist()
	def sync_fields(self):
		doctype_fields = dontmanage.get_meta(self.document_type).fields

		if self.is_new():
			added_fields = [field.fieldname for field in doctype_fields]
			removed_fields = []
		else:
			doctype_fieldnames = {field.fieldname for field in doctype_fields}
			layout_fieldnames = {field.fieldname for field in self.fields}
			added_fields = list(doctype_fieldnames - layout_fieldnames)
			removed_fields = list(layout_fieldnames - doctype_fieldnames)

		if not (added_fields or removed_fields):
			return

		added = self.add_fields(added_fields, doctype_fields)
		removed = self.remove_fields(removed_fields)

		for index, field in enumerate(self.fields):
			field.idx = index + 1

		return {"added": added, "removed": removed}

	def add_fields(self, added_fields: list[str], doctype_fields: list["DocField"]) -> list[dict]:
		added = []
		for field in added_fields:
			field_details = next((f for f in doctype_fields if f.fieldname == field), None)
			if not field_details:
				continue

			# remove 'doctype' data from the DocField to allow adding it to the layout
			row = self.append("fields", field_details.as_dict(no_default_fields=True))
			row_data = row.as_dict()

			if field_details.get("insert_after"):
				insert_after = next(
					(f for f in self.fields if f.fieldname == field_details.insert_after),
					None,
				)

				# initialize new row to just after the insert_after field
				if insert_after:
					self.fields.insert(insert_after.idx, row)
					self.fields.pop()

					row_data = {"idx": insert_after.idx + 1, "fieldname": row.fieldname, "label": row.label}

			added.append(row_data)
		return added

	def remove_fields(self, removed_fields: list[str]) -> list[dict]:
		removed = []
		for field in removed_fields:
			field_details = next((f for f in self.fields if f.fieldname == field), None)
			if field_details:
				self.remove(field_details)
				removed.append(field_details.as_dict())
		return removed
