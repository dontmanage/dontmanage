# Copyright (c) 2021, DontManage Technologies and contributors
# License: MIT. See LICENSE

# import dontmanage
from dontmanage.model.document import Document


class WorkspaceShortcut(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		color: DF.Color | None
		doc_view: DF.Literal["", "List", "Report Builder", "Dashboard", "Tree", "New", "Calendar", "Kanban"]
		format: DF.Data | None
		icon: DF.Data | None
		kanban_board: DF.Link | None
		label: DF.Data
		link_to: DF.DynamicLink | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		restrict_to_domain: DF.Link | None
		stats_filter: DF.Code | None
		type: DF.Literal["DocType", "Report", "Page", "Dashboard", "URL"]
		url: DF.Data | None
	# end: auto-generated types
	pass
