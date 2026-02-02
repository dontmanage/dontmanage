import dontmanage
from dontmanage.utils.install import add_standard_navbar_items


def execute():
	# Add standard navbar items for DontManageErp in Navbar Settings
	dontmanage.reload_doc("core", "doctype", "navbar_settings")
	dontmanage.reload_doc("core", "doctype", "navbar_item")
	add_standard_navbar_items()
