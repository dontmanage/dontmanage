# Copyright (c) 2021, DontManage Technologies and contributors
# For license information, please see license.txt

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document


class PrintFormatFieldTemplate(Document):
	def validate(self):
		if self.standard and not (dontmanage.conf.developer_mode or dontmanage.flags.in_patch):
			dontmanage.throw(_("Enable developer mode to create a standard Print Template"))

	def before_insert(self):
		self.validate_duplicate()

	def on_update(self):
		self.validate_duplicate()
		self.export_doc()

	def validate_duplicate(self):
		if not self.standard:
			return
		if not self.field:
			return

		filters = {"document_type": self.document_type, "field": self.field}
		if not self.is_new():
			filters.update({"name": ("!=", self.name)})
		result = dontmanage.get_all("Print Format Field Template", filters=filters, limit=1)
		if result:
			dontmanage.throw(
				_("A template already exists for field {0} of {1}").format(
					dontmanage.bold(self.field), dontmanage.bold(self.document_type)
				),
				dontmanage.DuplicateEntryError,
				title=_("Duplicate Entry"),
			)

	def export_doc(self):
		from dontmanage.modules.utils import export_module_json

		export_module_json(self, self.standard, self.module)
