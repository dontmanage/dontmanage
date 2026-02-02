# Copyright (c) 2025, DontManage Technologies and contributors
# For license information, please see license.txt

# import dontmanage
from dontmanage.model.document import Document


class EventNotifications(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		before: DF.Int
		interval: DF.Literal[None]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		time: DF.Time | None
		type: DF.Literal["Notification", "Email"]
	# end: auto-generated types

	pass
