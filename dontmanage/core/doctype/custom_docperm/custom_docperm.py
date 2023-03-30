# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class CustomDocPerm(Document):
	def on_update(self):
		dontmanage.clear_cache(doctype=self.parent)
