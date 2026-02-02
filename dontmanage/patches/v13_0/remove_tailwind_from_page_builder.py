# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.reload_doc("website", "doctype", "web_page_block")
	# remove unused templates
	dontmanage.delete_doc("Web Template", "Navbar with Links on Right", force=1)
	dontmanage.delete_doc("Web Template", "Footer Horizontal", force=1)
