# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document
from dontmanage.modules.export_file import export_to_files


class ModuleOnboarding(Document):
	def on_update(self):
		if dontmanage.conf.developer_mode:
			export_to_files(record_list=[["Module Onboarding", self.name]], record_module=self.module)

			for step in self.steps:
				export_to_files(record_list=[["Onboarding Step", step.step]], record_module=self.module)

	def get_steps(self):
		return [dontmanage.get_doc("Onboarding Step", step.step) for step in self.steps]

	def get_allowed_roles(self):
		all_roles = [role.role for role in self.allow_roles]
		if "System Manager" not in all_roles:
			all_roles.append("System Manager")

		return all_roles

	def check_completion(self):
		if self.is_complete:
			return True

		steps = self.get_steps()
		is_complete = [bool(step.is_complete or step.is_skipped) for step in steps]
		if all(is_complete):
			self.is_complete = True
			self.save()
			return True

		return False

	def before_export(self, doc):
		doc.is_complete = 0

	def reset_onboarding(self):
		dontmanage.only_for("Administrator")

		self.is_complete = 0
		steps = self.get_steps()
		for step in steps:
			step.is_complete = 0
			step.is_skipped = 0
			step.save()

		self.save()
