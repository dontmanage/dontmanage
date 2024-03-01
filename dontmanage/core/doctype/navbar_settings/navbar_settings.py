# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document


class NavbarSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.core.doctype.navbar_item.navbar_item import NavbarItem
		from dontmanage.types import DF

		app_logo: DF.AttachImage | None
		help_dropdown: DF.Table[NavbarItem]
		logo_width: DF.Int
		settings_dropdown: DF.Table[NavbarItem]

	# end: auto-generated types
	def validate(self):
		self.validate_standard_navbar_items()

	def validate_standard_navbar_items(self):
		doc_before_save = self.get_doc_before_save()

		if not doc_before_save:
			return

		before_save_items = [
			item
			for item in doc_before_save.help_dropdown + doc_before_save.settings_dropdown
			if item.is_standard
		]

		after_save_items = [item for item in self.help_dropdown + self.settings_dropdown if item.is_standard]

		if not dontmanage.flags.in_patch and (len(before_save_items) > len(after_save_items)):
			dontmanage.throw(_("Please hide the standard navbar items instead of deleting them"))


def get_app_logo():
	app_logo = dontmanage.db.get_single_value("Navbar Settings", "app_logo", cache=True)
	if not app_logo:
		app_logo = dontmanage.get_hooks("app_logo_url")[-1]

	return app_logo


def get_navbar_settings():
	return dontmanage.get_single("Navbar Settings")
