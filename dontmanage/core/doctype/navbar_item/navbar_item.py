# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

# import dontmanage
from dontmanage.model.document import Document


class NavbarItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		action: DF.Data | None
		hidden: DF.Check
		is_standard: DF.Check
		item_label: DF.Data | None
		item_type: DF.Literal["Route", "Action", "Separator"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		route: DF.Data | None
	# end: auto-generated types
	pass
