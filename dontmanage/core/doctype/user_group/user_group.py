# Copyright (c) 2021, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage

# import dontmanage
from dontmanage.model.document import Document


class UserGroup(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.core.doctype.user_group_member.user_group_member import UserGroupMember
		from dontmanage.types import DF

		user_group_members: DF.TableMultiSelect[UserGroupMember]

	# end: auto-generated types
	def after_insert(self):
		dontmanage.cache.delete_key("user_groups")

	def on_trash(self):
		dontmanage.cache.delete_key("user_groups")
