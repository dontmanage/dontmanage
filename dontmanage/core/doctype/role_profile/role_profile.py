# Copyright (c) 2017, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class RoleProfile(Document):
	def autoname(self):
		"""set name as Role Profile name"""
		self.name = self.role_profile

	def on_update(self):
		"""Changes in role_profile reflected across all its user"""
		users = dontmanage.get_all("User", filters={"role_profile_name": self.name})
		roles = [role.role for role in self.roles]
		for d in users:
			user = dontmanage.get_doc("User", d)
			user.set("roles", [])
			user.add_roles(*roles)
