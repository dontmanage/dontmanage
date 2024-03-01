# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class TopBarItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		label: DF.Data
		open_in_new_tab: DF.Check
		parent: DF.Data
		parent_label: DF.Literal
		parentfield: DF.Data
		parenttype: DF.Data
		right: DF.Check
		url: DF.Data | None
	# end: auto-generated types

	pass
