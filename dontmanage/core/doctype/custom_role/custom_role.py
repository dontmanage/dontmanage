# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class CustomRole(Document):
	def validate(self):
		if self.report and not self.ref_doctype:
			self.ref_doctype = dontmanage.db.get_value("Report", self.report, "ref_doctype")


def get_custom_allowed_roles(field, name):
	allowed_roles = []
	custom_role = dontmanage.db.get_value("Custom Role", {field: name}, "name")
	if custom_role:
		custom_role_doc = dontmanage.get_doc("Custom Role", custom_role)
		allowed_roles = [d.role for d in custom_role_doc.roles]

	return allowed_roles
