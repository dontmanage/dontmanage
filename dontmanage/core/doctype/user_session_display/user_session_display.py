# Copyright (c) 2025, DontManage Technologies and contributors
# For license information, please see license.txt

# import dontmanage
from dontmanage.model.document import Document


class UserSessionDisplay(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		id: DF.Data | None
		ip_address: DF.Data | None
		is_current: DF.Check
		last_updated: DF.Datetime | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		session_created: DF.Datetime | None
		user_agent: DF.SmallText | None
	# end: auto-generated types

	def db_insert(self, *args, **kwargs):
		raise NotImplementedError

	def load_from_db(self, *args, **kwargs):
		raise NotImplementedError

	def db_update(self, *args, **kwargs):
		raise NotImplementedError

	def delete(self, *args, **kwargs):
		raise NotImplementedError
