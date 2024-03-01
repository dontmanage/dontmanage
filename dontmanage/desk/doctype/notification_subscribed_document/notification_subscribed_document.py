# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

# import dontmanage
from dontmanage.model.document import Document


class NotificationSubscribedDocument(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		document: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types
	pass
