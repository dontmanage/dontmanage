# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class WebsiteSidebarItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		group: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		route: DF.Data | None
		title: DF.Data
	# end: auto-generated types
	pass
