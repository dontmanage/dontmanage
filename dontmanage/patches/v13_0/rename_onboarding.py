# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage


def execute():
	if dontmanage.db.exists("DocType", "Onboarding"):
		dontmanage.rename_doc("DocType", "Onboarding", "Module Onboarding", ignore_if_exists=True)
