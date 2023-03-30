# Copyright (c) 2021, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage

# import dontmanage
from dontmanage.model.document import Document


class UserGroup(Document):
	def after_insert(self):
		dontmanage.cache().delete_key("user_groups")

	def on_trash(self):
		dontmanage.cache().delete_key("user_groups")
