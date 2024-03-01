# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

# import dontmanage
from dontmanage.model.document import Document


class DocTypeLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		custom: DF.Check
		group: DF.Data | None
		hidden: DF.Check
		is_child_table: DF.Check
		link_doctype: DF.Link
		link_fieldname: DF.Data
		parent: DF.Data
		parent_doctype: DF.Link | None
		parentfield: DF.Data
		parenttype: DF.Data
		table_fieldname: DF.Data | None
	# end: auto-generated types
	pass
