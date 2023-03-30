# Copyright (c) 2017, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class PrintStyle(Document):
	def validate(self):
		if (
			self.standard == 1
			and not dontmanage.local.conf.get("developer_mode")
			and not (dontmanage.flags.in_import or dontmanage.flags.in_test)
		):

			dontmanage.throw(dontmanage._("Standard Print Style cannot be changed. Please duplicate to edit."))

	def on_update(self):
		self.export_doc()

	def export_doc(self):
		# export
		from dontmanage.modules.utils import export_module_json

		export_module_json(self, self.standard == 1, "Printing")
