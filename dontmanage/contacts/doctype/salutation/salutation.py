# Copyright (c) 2017, DontManage Technologies and contributors
# License: MIT. See LICENSE

from dontmanage.model.document import Document


class Salutation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		salutation: DF.Data | None
	# end: auto-generated types
	pass
