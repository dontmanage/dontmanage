# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage
from dontmanage.model.document import Document


class ClientScript(Document):
	def on_update(self):
		dontmanage.clear_cache(doctype=self.dt)

	def on_trash(self):
		dontmanage.clear_cache(doctype=self.dt)
