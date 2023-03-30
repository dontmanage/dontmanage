# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class HasRole(Document):
	def before_insert(self):
		if dontmanage.db.exists("Has Role", {"parent": self.parent, "role": self.role}):
			dontmanage.throw(dontmanage._("User '{0}' already has the role '{1}'").format(self.parent, self.role))
