# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.reload_doc("core", "doctype", "system_settings", force=1)
	dontmanage.db.set_single_value("System Settings", "password_reset_limit", 3)
