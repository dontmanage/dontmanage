# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import json
import os

import dontmanage
from dontmanage.model.document import Document


class ModuleDef(Document):
	def on_update(self):
		"""If in `developer_mode`, create folder for module and
		add in `modules.txt` of app if missing."""
		dontmanage.clear_cache()
		if not self.custom and dontmanage.conf.get("developer_mode"):
			self.create_modules_folder()
			self.add_to_modules_txt()

	def create_modules_folder(self):
		"""Creates a folder `[app]/[module]` and adds `__init__.py`"""
		module_path = dontmanage.get_app_path(self.app_name, self.name)
		if not os.path.exists(module_path):
			os.mkdir(module_path)
			with open(os.path.join(module_path, "__init__.py"), "w") as f:
				f.write("")

	def add_to_modules_txt(self):
		"""Adds to `[app]/modules.txt`"""
		modules = None
		if not dontmanage.local.module_app.get(dontmanage.scrub(self.name)):
			with open(dontmanage.get_app_path(self.app_name, "modules.txt")) as f:
				content = f.read()
				if not self.name in content.splitlines():
					modules = list(filter(None, content.splitlines()))
					modules.append(self.name)

			if modules:
				with open(dontmanage.get_app_path(self.app_name, "modules.txt"), "w") as f:
					f.write("\n".join(modules))

				dontmanage.clear_cache()
				dontmanage.setup_module_map()

	def on_trash(self):
		"""Delete module name from modules.txt"""

		if not dontmanage.conf.get("developer_mode") or dontmanage.flags.in_uninstall or self.custom:
			return

		modules = None
		if dontmanage.local.module_app.get(dontmanage.scrub(self.name)):
			with open(dontmanage.get_app_path(self.app_name, "modules.txt")) as f:
				content = f.read()
				if self.name in content.splitlines():
					modules = list(filter(None, content.splitlines()))
					modules.remove(self.name)

			if modules:
				with open(dontmanage.get_app_path(self.app_name, "modules.txt"), "w") as f:
					f.write("\n".join(modules))

				dontmanage.clear_cache()
				dontmanage.setup_module_map()


@dontmanage.whitelist()
def get_installed_apps():
	return json.dumps(dontmanage.get_installed_apps())
