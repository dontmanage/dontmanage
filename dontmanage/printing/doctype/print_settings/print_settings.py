# Copyright (c) 2018, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document
from dontmanage.utils import cint


class PrintSettings(Document):
	def validate(self):
		if self.pdf_page_size == "Custom" and not (self.pdf_page_height and self.pdf_page_width):
			dontmanage.throw(_("Page height and width cannot be zero"))

	def on_update(self):
		dontmanage.clear_cache()


@dontmanage.whitelist()
def is_print_server_enabled():
	if not hasattr(dontmanage.local, "enable_print_server"):
		dontmanage.local.enable_print_server = cint(
			dontmanage.db.get_single_value("Print Settings", "enable_print_server")
		)

	return dontmanage.local.enable_print_server
