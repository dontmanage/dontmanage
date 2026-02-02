# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	dontmanage.reload_doc("core", "doctype", "system_settings")
	dontmanage.db.set_single_value("System Settings", "allow_login_after_fail", 60)
