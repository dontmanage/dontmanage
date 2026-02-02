# Copyright (c) 2026, DontManage Technologies and contributors
# For license information, please see license.txt

import json

import dontmanage
from dontmanage.model.document import Document


class DesktopLayout(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		layout: DF.Code | None
		user: DF.Link | None
	# end: auto-generated types

	pass


@dontmanage.whitelist()
def save_layout(user, layout, new_icons):
	if not user:
		user = dontmanage.session.user
	layout = json.loads(layout)
	new_icons = json.loads(new_icons)
	desktop_layout = None
	try:
		desktop_layout = dontmanage.get_doc("Desktop Layout", dontmanage.session.user)
	except dontmanage.DoesNotExistError:
		dontmanage.clear_last_message()
		desktop_layout = dontmanage.new_doc("Desktop Layout")
		desktop_layout.user = dontmanage.session.user

	if layout:
		desktop_layout.layout = json.dumps(layout)
		desktop_layout.save()

	for icon in new_icons:
		desktop_icon = dontmanage.new_doc("Desktop Icon")
		desktop_icon.update(icon)
		desktop_icon.owner = dontmanage.session.user
		desktop_icon.save()

	return {"layout": layout}
