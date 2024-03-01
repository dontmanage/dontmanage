# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document
from dontmanage.modules.export_file import export_to_files


class ModuleOnboarding(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.desk.doctype.onboarding_permission.onboarding_permission import OnboardingPermission
		from dontmanage.desk.doctype.onboarding_step_map.onboarding_step_map import OnboardingStepMap
		from dontmanage.types import DF

		allow_roles: DF.TableMultiSelect[OnboardingPermission]
		documentation_url: DF.Data
		is_complete: DF.Check
		module: DF.Link
		steps: DF.Table[OnboardingStepMap]
		subtitle: DF.Data
		success_message: DF.Data
		title: DF.Data

	# end: auto-generated types
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
			self.save(ignore_permissions=True)
			return True

		return False

	@dontmanage.whitelist()
	def reset_progress(self):
		self.db_set("is_complete", 0)

		for step in self.get_steps():
			step.db_set("is_complete", 0)
			step.db_set("is_skipped", 0)

		dontmanage.msgprint(_("Module onboarding progress reset"), alert=True)

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
