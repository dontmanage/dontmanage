# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

# import dontmanage
from dontmanage.model.document import Document


class WebTemplateField(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		default: DF.SmallText | None
		fieldname: DF.Data | None
		fieldtype: DF.Literal[
			"Attach Image",
			"Check",
			"Data",
			"Int",
			"Link",
			"Select",
			"Small Text",
			"Text",
			"Markdown Editor",
			"Section Break",
			"Column Break",
			"Table Break",
		]
		label: DF.Data
		options: DF.SmallText | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		reqd: DF.Check
	# end: auto-generated types
	pass
