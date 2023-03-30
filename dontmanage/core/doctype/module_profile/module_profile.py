# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

from dontmanage.model.document import Document


class ModuleProfile(Document):
	def onload(self):
		from dontmanage.config import get_modules_from_all_apps

		self.set_onload("all_modules", [m.get("module_name") for m in get_modules_from_all_apps()])
