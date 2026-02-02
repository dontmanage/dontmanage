# Copyright (c) 2025, DontManage Technologies and contributors
# For license information, please see license.txt

# import dontmanage
from dontmanage.model.document import Document


class DesktopSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		icon_style: DF.Literal["Subtle", "Solid"]
	# end: auto-generated types

	pass
